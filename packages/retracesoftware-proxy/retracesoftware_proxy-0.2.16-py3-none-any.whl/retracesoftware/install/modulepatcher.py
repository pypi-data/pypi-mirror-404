import retracesoftware.utils as utils
import retracesoftware.functional as functional
from functools import wraps
import inspect
import gc
import importlib
import types
import sys

from retracesoftware.proxy.thread import start_new_thread_wrapper, counters
from retracesoftware.install.typeutils import modify

def find_attr(mro, name):
    for cls in mro:
        if name in cls.__dict__:
            return cls.__dict__[name]

def is_descriptor(obj):
    return hasattr(obj, '__get__') or hasattr(obj, '__set__') or hasattr(obj, '__delete__')

def resolve(path):
    module, sep, name = path.rpartition('.')
    if module == None: module = 'builtins'
    
    return getattr(importlib.import_module(module), name)

def phase(func):
    func.is_phase = True  # add marker attribute
    return func

def replace(replacements, coll):
    return map(lambda x: replacements.get(x, x), coll)

def container_replace(container, old, new):
    if isinstance(container, dict):
        if old in container:
            elem = container.pop(old)
            container[new] = elem
            container_replace(container, old, new)
        else:
            for key,value in container.items():
                if key != '__retrace_unproxied__' and value is old:
                    container[key] = new
        return True
    elif isinstance(container, list):
        for i,value in enumerate(container):
            if value is old:
                container[i] = new
        return True
    elif isinstance(container, set):
        container.remove(old)
        container.add(new)
        return True
    else:
        return False

def select_keys(keys, dict):
    return {key: dict[key] for key in keys if key in dict}

def map_values(f, dict):
    return {key: f(value) for key,value in dict.items()}

def common_keys(dict, *dicts):
    common_keys = utils.set(dict)
    for d in dicts:
        common_keys &= d.keys()

    assert isinstance(common_keys, utils.set)

    return common_keys

def intersection(*dicts):
    return { key: tuple(d[key] for d in dicts) for key in common_keys(*dicts) }

def intersection_apply(f, *dicts):
    return map_values(lambda vals: f(*vals), intersection(*dicts))

def patch(func):
    @wraps(func)
    def wrapper(self, spec, mod_dict):
        if isinstance(spec, str):
            return wrapper(self, [spec], mod_dict)
        elif isinstance(spec, list):
            res = {}
            for name in spec:
                if name in mod_dict:
                    value = func(self, mod_dict[name])
                    if value is not None:
                        res[name] = value
            return res
        elif isinstance(spec, dict):
            # return {name: func(self, mod_dict[name], value) for name, value in spec.items() if name in mod_dict}
            res = {}
            for name,value in spec.items():
                if name in mod_dict:
                    value = func(self, mod_dict[name], value)
                    if value is not None:
                        res[name] = value
            return res
        else:
            raise Exception('TODO')

    wrapper.is_phase = True  
    return wrapper

def is_special(name):
    return len(name) > 4 and name.startswith('__') and name.endswith('__')

def superdict(cls):
    result = {}
    for cls in list(reversed(cls.__mro__))[1:]:
        result.update(cls.__dict__)
    
    return result

def wrap_method_descriptors(wrapper, prefix, base):
    slots = {"__slots__": () }

    extended = type(f'{prefix}.{base.__module__}.{base.__name__}', (base,), {"__slots__": () })

    blacklist = ['__getattribute__', '__hash__', '__del__']

    for name,value in superdict(base).items():
        if name not in blacklist:
            if utils.is_method_descriptor(value):
                setattr(extended, name, wrapper(value))

    return extended

class ElementPatcher:

    def __init__(self, config, phases):
        funcs = {}

        for phase in phases:
            if phase.name in config:
                for key,func in phase(config[phase.name]).items():
                    val = funcs.get(key, [])
                    val.append(func)
                    funcs[key] = val

        self.funcs = utils.map_values(lambda funcs: functional.sequence(*funcs), funcs)
        self.fallback = None

        if 'default' in config:
            default_name = config['default']
            for phase in phases:
                if phase.name == default_name:
                    self.fallback = phase.patch
            
    def __call__(self, name, value):
        if name in self.funcs:
            return self.funcs[name](value)
        elif not is_special(name) and self.fallback:
            return self.fallback(value)
        else:
            return value

# class Patcher:

#     def __init__(self, config):
        
#         self.config = config
#         self.phases = []
#         self.patched = {}

#         # system.set_thread_id(0)
#         # self.thread_counter = system.sync(utils.counter(1))
#         # self.module_config = module_config

#         # self.thread_state = thread_state
#         # self.debug_level = debug_level
#         # self.on_function_proxy = on_function_proxy
#         # self.modules = config['modules']
#         # self.immutable_types_set = immutable_types
#         # self.predicate = PredicateBuilder()
#         # self.system = system        
#         # self.type_attribute_filter = self.predicate(config['type_attribute_filter'])
#         # self.post_commit = post_commit
#         # self.exclude_paths = [re.compile(s) for s in config.get('exclude_paths', [])]
#         # self.typepatcher = {}
#         # self.originals = {}

#         # def is_phase(name): return getattr(getattr(self, name, None), "is_phase", False)
        
#         # self.phases = [(name, getattr(self, name)) for name in Patcher.__dict__.keys() if is_phase(name)]

#     def add_phase(self, phase):
#         self.phases.append(phase)

#     # def log(self, *args):
#     #     self.system.tracer.log(*args)

#     def path_predicate(self, path):
#         for exclude in self.exclude_paths:
#             if exclude.match(str(path)) is not None:
#                 # print(f'in path_predicate, excluding {path}')
#                 return False
#         return True

#     # def on_proxytype(self, cls):

#     #     def patch(spec):
#     #         for method, transform in spec.items():                
#     #             setattr(cls, method, resolve(transform)(getattr(cls, method)))

#     #     if cls.__module__ in self.modules:
#     #         spec = self.modules[cls.__module__]

#     #         if 'patchtype' in spec:
#     #             patchtype = spec['patchtype']
#     #             if cls.__name__ in patchtype:
#     #                 patch(patchtype[cls.__name__])

#     @property
#     def disable(self):
#         return self.thread_state.select('disabled')
    
#     def proxyable(self, name, obj):
#         if name.startswith('__') and name.endswith('__'):
#             return False
        
#         if isinstance(obj, (str, int, dict, list, tuple)):
#             return False
        
#         if isinstance(obj, type):
#             return not issubclass(obj, BaseException) and obj not in self.immutable_types_set

class Patcher:

    def __init__(self, config):
        
        self.config = config
        self.phases = []
        self.patched = {}

    def add_phase(self, phase):
        self.phases.append(phase)

    def path_predicate(self, path):
        for exclude in self.exclude_paths:
            if exclude.match(str(path)) is not None:
                # print(f'in path_predicate, excluding {path}')
                return False
        return True

    @property
    def disable(self):
        return self.thread_state.select('disabled')
    
    def proxyable(self, name, obj):
        if name.startswith('__') and name.endswith('__'):
            return False
        
        if isinstance(obj, (str, int, dict, list, tuple)):
            return False
        
        if isinstance(obj, type):
            return not issubclass(obj, BaseException) and obj not in self.immutable_types_set
        else:
            return type(obj) not in self.immutable_types_set

    @phase
    def proxy_type_attributes(self, spec, mod_dict):
        for classname, attributes in spec.items():
            if classname in mod_dict:
                cls = mod_dict[classname]
                if isinstance(cls, type):
                    for name in attributes:
                        attr = find_attr(cls.__mro__, name)
                        if attr is not None and (callable(attr) or is_descriptor(attr)):
                            proxied = self.system(attr)
                            # proxied = self.proxy(attr)

                            with modify(cls):
                                setattr(cls, name, proxied)
                else:
                    raise Exception(f"Cannot patch attributes for {cls.__module__}.{cls.__name__} as object is: {cls} and not a type")

    @phase
    def replace(self, spec, mod_dict):
        return {key: resolve(value) for key,value in spec.items()}

    @patch
    def patch_start_new_thread(self, value):
        return start_new_thread_wrapper(thread_state = self.thread_state, 
                                        on_exit = self.system.on_thread_exit,
                                        start_new_thread = value)
    
        # def start_new_thread(function, *args):
        #     # synchronized, replay shoudl yield correct number
        #     thread_id = self.thread_counter()

        #     def threadrunner(*args, **kwargs):
        #         nonlocal thread_id
        #         self.system.set_thread_id(thread_id)
                
        #         with self.thread_state.select('internal'):
        #             try:
        #                 # if self.tracing:
        #                 #     FrameTracer.install(self.thread_state.dispatch(noop, internal = self.checkpoint))    
        #                 return function(*args, **kwargs)
        #             finally:
        #                 print(f'exiting: {thread_id}')

        #     return value(threadrunner, *args)

        # return self.thread_state.dispatch(value, internal = start_new_thread)

    @phase
    def wrappers(self, spec, mod_dict): 
        return intersection_apply(lambda path, value: resolve(path)(value), spec, mod_dict)

    @patch
    def patch_exec(self, exec):

        def is_module(source, *args):
            return isinstance(source, types.CodeType) and source.co_name == '<module>'
        
        def after_exec(source, globals = None, locals = None):
            if isinstance(source, types.CodeType) and source.co_name == '<module>' and '__name__' in globals:
                self(sys.modules[globals['__name__']])
        
        def first(x): return x[0]
            
        def disable(func): return self.thread_state.wrap('disabled', func)
    
        return self.thread_state.dispatch(
            exec, 
            internal = functional.sequence(
                functional.juxt(exec, functional.when(is_module, disable(after_exec))), first))
    
    # self.thread_state.wrap(desired_state = 'disabled', function = exec_wrapper)

    @patch
    def sync_types(self, value):
        return wrap_method_descriptors(self.system.sync, "retrace", value)

    @phase
    def with_state_recursive(self, spec, mod_dict):

        updates = {}

        for state,elems in spec.items():

            def wrap(obj): 
                return functional.recurive_wrap_function(
                    functional.partial(self.thread_state.wrap, state),
                    obj)
            
            updates.update(map_values(wrap, select_keys(elems, mod_dict)))
        
        return updates

    @phase
    def methods_with_state(self, spec, mod_dict):

        # updates = {}

        def update(cls, name, f):
            setattr(cls, name, f(getattr(cls, name)))

        for state,cls_methods in spec.items():
            def wrap(obj): 
                assert callable(obj)
                return self.thread_state.wrap(desired_state = state, function = obj)

            for typename,methodnames in cls_methods.items():
                cls = mod_dict[typename]

                for methodname in methodnames:
                    update(cls, methodname, wrap)
        
        return {}

    @phase
    def with_state(self, spec, mod_dict):

        updates = {}

        for state,elems in spec.items():

            def wrap(obj): 
                return self.thread_state.wrap(desired_state = state, function = obj)

            updates.update(map_values(wrap, select_keys(elems, mod_dict)))
        
        return updates

    @patch
    def patch_extension_exec(self, exec):
        
        def first(x): return x[0]

        def disable(func): return self.thread_state.wrap('disabled', func)
    
        return self.thread_state.dispatch(exec, 
                                   internal = functional.sequence(functional.juxt(exec, disable(self)), first))
        
        # def wrapper(module):
        #     with self.thread_state.select('internal'):
        #         res = exec(module)

        #     self(module)
        #     return res

        # return wrapper

    @patch
    def path_predicates(self, func, param):
        signature = inspect.signature(func).parameters

        try:
            index = list(signature.keys()).index(param)
        except ValueError:
            print(f'parameter {param} not in: {signature.keys()} {type(func)} {func}')
            raise
        
        param = functional.param(name = param, index = index)

        assert callable(param)
        
        return functional.if_then_else(
            test = functional.sequence(param, self.path_predicate),
            then = func, 
            otherwise = self.thread_state.wrap('disabled', func)) 
        
    @phase
    def wrap(self, spec, mod_dict):
        updates = {}

        for path, wrapper_name in spec.items():

            parts = path.split('.')
            name = parts[0]
            if name in mod_dict:
                value = mod_dict[name]
                assert not isinstance(value, utils.wrapped_function), \
                    f"value for key: {name} is already wrapped"
                
                if len(parts) == 1:
                    updates[name] = resolve(wrapper_name)(value)
                elif len(parts) == 2:
                    member = getattr(value, parts[1], None)
                    if member:
                        new_value = resolve(wrapper_name)(member)
                        setattr(value, parts[1], new_value)
                else:
                    raise Exception('TODO')
                
        return updates

    def find_phase(self, name):
        for phase in self.phases:
            if phase.name == name:
                return phase

        raise Exception(f'Phase: {name} not found')

    # def run_transforms(self, config, obj):
    #     if isinstance(config, str):
    #         return find_phase(config).patch(obj)
    #     else:
    #         for name in config

    def element_patcher(self, name):
        if name in self.config:
            return ElementPatcher(config = self.config[name], 
                                  phases = self.phases)

    def wrap_namespace(self, ns):
        name = ns.get('__name__', None)
        patcher = self.element_patcher(name)
        print(f'wrap_namespace {name} {patcher}')
        return utils.InterceptDict(ns, patcher) if patcher else ns

    def update(self, old, new):
        if isinstance(new, type) and isinstance(old, type) and issubclass(new, old):
            for subclass in old.__subclasses__():
                if subclass is not new:
                    subclass.__bases__ = tuple(replace({old: new}, subclass.__bases__))

        for ref in gc.get_referrers(old):
            container_replace(container = ref, old = old, new = new)

    def patch_loaded_module(self, mod_dict):
        modname = mod_dict.get('__name__', None)
        
        print(f'Patching loaded module: {modname}')

        if modname in self.config:
            

            originals = {}
            self.patched[modname] = originals

            patcher = self.element_patcher(modname)

            for key in list(mod_dict.keys()):
                original = mod_dict[key]
                patched = patcher(key, original)

                if patched is not original:
                    self.update(old = original, new = patched)
                    originals[key] = original
                    assert mod_dict[key] is patched
