from xml.etree import ElementTree
from collections import OrderedDict
import io
import re

tree = ElementTree.parse('vk.xml').getroot()

defined_defs = {'void', 'char', 'float', 'uint8_t', 'uint32_t', 'uint64_t', 'int32_t', 'size_t', 'DWORD', 'HINSTANCE', 'HWND', 'HANDLE'}

external_structs = {'Display', 'xcb_connection_t', 'wl_display', 'wl_surface', 'MirConnection', 'MirSurface', 'ANativeWindow', 'SECURITY_ATTRIBUTES'}
handle_defs = {'Window': 'uint32_t',
                'VisualID': 'uint32_t',
                'xcb_window_t': 'uint32_t',
                'xcb_visualid_t': 'uint32_t',
                }

platform_protects = {'linux': ('VK_USE_PLATFORM_XLIB_KHR', 'VK_USE_PLATFORM_XCB_KHR', 'VK_USE_PLATFORM_WAYLAND_KHR', 'VK_USE_PLATFORM_MIR_KHR'),
            'win32': ('VK_USE_PLATFORM_WIN32_KHR', ),
            'android': ('VK_USE_PLATFORM_ANDROID_KHR')}

platform_defs = {'linux': {'Display', 'Window', 'VisualID', 'xcb_connection_t', 'xcb_window_t', 'xcb_visualid_t', 'wl_display', 'wl_surface', 'MirConnection', 'MirSurface'},
                'win32': {'SECURITY_ATTRIBUTES'},
                'android': {'ANativeWindow'}}
extension_types = {}
platform_extensions = {k: set() for k in platform_protects}
general_extensions = set()

ext_base = 1000000000
ext_block_size = 1000

typedefs = {}
struct_unions = {}
macros = {}
enums = {}
funcpointers = {}
funcs = {}
ext_funcs = {}

structs_default_values = {}
structs_len_autos = {}


def innertext(tag):
    return (tag.text or '') + ''.join(innertext(e) for e in tag) + (tag.tail or '')

for i in tree.findall('types/type'):
    name = i.get('name')
    requires = i.get('requires')
    category = i.get('category')
    if category in {'struct', 'union'}:
        members = i.findall('member')


        def _(elem):
            if elem is None:
                return None
            return elem.text
        struct_unions[name] = (category, [((j.find('type').text + (j.find('type').tail or '')).strip(), j.find('name').text, _(j.find('enum'))) for j in members])
        structs_default_values[name] = {j.find('name').text: j.get('values') for j in members if j.get('values')}
        structs_len_autos[name] = {}
        member_names = [j.find('name').text for j in members]
        for j in members:
            len_ = j.get('len')
            name_ = j.find('name').text
            if len_:
                lens = [i for i in len_.split(',') if i != 'null-terminated']
                if len(lens) == 1:
                    if lens[0] in member_names:
                        assert not (name_ in structs_default_values[name])
                        structs_default_values[name][name_] = []
                        if not lens[0] in structs_len_autos[name]:
                            structs_len_autos[name][lens[0]] = []
                        structs_len_autos[name][lens[0]].append("len(%s)" % name_)
                else:
                    assert not lens
    elif category == 'bitmask':
        typedefs[i.find('name').text] = (i.find('type').text, i.find('name').text)
    elif category == 'include':
        pass
    elif category == 'define':
        name = i.find('name')
        if name is None:
            continue
        # print>>linux_header, innertext(i).strip()
    elif category == 'basetype':
        typedefs[i.find('name').text] = (i.find('type').text, i.find('name').text)
    elif category == 'handle':
        type_ = i.find('type').text
        name = i.find('name').text
        if type_ == 'VK_DEFINE_HANDLE':
            typedefs[name] = ('struct %s_T' % name, '*%s' % name)
        elif type_ == 'VK_DEFINE_NON_DISPATCHABLE_HANDLE':
            # FIXME
            typedefs[name] = ('uint64_t', name)
        else:
            assert False
    elif category == 'enum':
        name = i.get('name')
        enums[name] = {}
    elif category == 'funcpointer':
        funcpointers[i.find('name').text] = ' '.join(innertext(i).split()).replace('( ', '(').strip()
    elif category is None:
        requires = i.get('requires')
        if requires is None:
            continue

        platform = None
        if requires in {'X11/Xlib.h', 'mir_toolkit/client_types.h', 'wayland-client.h', 'xcb/xcb.h'}:
            platform = 'linux'
        elif requires == 'windows.h':
            platform = 'win32'
        elif requires == 'android/native_window.h':
            platform = 'android'
        else:
            assert requires == 'vk_platform'

        if not platform is None:
            platform_extensions[platform].add(name)

        if name in external_structs:
            typedefs[name] = ("struct %s" % name, name)
        elif name in handle_defs:
            typedefs[name] = (handle_defs[name], name)
        else:
            assert name in defined_defs
    else:
        assert False


def evalEnum(enum, number=0):
    if 'value' in enum.attrib:
        value = enum.attrib['value']
        special_cases = {'1000.0f': '1000.0', '(~0U)': -1, '(~0ULL)': -1}
        if value in special_cases:
            return special_cases[value]
        return value
    elif 'bitpos' in enum.attrib:
        return 1 << int(enum.attrib['bitpos'])
    elif 'extends' in enum.attrib:
        sign = -1 if enum.get('dir') == '-' else 1
        return sign * (ext_base + ext_block_size * (number - 1) + int(enum.attrib['offset']))
    else:
        assert False

enum_types = {}

for i in tree.findall('enums'):
    type_ = i.get('type')
    if type_ in ('enum', 'bitmask'):
        name = i.attrib['name']
        enum_types[name] = type_
        for j in i.findall('enum'):
            enums[name][j.attrib['name']] = evalEnum(j)
    else:
        for j in i.findall('enum'):
            macros[j.attrib['name']] = evalEnum(j)

pattern = re.compile('(.*?)([A-Z]*)$')

enums_ranges = {}

for i in enums:
    if i!='VkCompositeAlphaFlagBitsKHR':
        continue
    if not enums[i]:
        continue

    name = pattern.match(i).group(1)
    ext = pattern.match(i).group(2)
    postfix = '_' + ext if ext else ''

    def _(name):
        upper_pos = [j for j, k in enumerate(name) if k.isupper()]
        return '_'.join(name[begin:end].upper() for begin, end in zip(upper_pos, upper_pos[1:] + [len(name)])) + '_'

    is_bitmask = enum_types[i] == 'bitmask'
    if is_bitmask:
        assert name.endswith('FlagBits')
        prefix = _(name[:-8])
        enums_ranges[i] = {prefix+'FLAG_BITS_MAX_ENUM'+postfix:0x7FFFFFFF}
    else:
        prefix = _(name)
        values = [int(j) for _, j in enums[i].items()]
        enums_ranges[i] = {prefix + 'BEGIN_RANGE' + postfix:min(values),
                        prefix + 'END_RANGE' + postfix:max(values),
                        prefix + 'RANGE_SIZE' + postfix:max(values)-min(values)+1,
                        prefix + 'MAX_ENUM' + postfix:0x7FFFFFFF}


for i in tree.findall('extensions/extension'):
    #TODO:add extension macro
    if i.attrib['supported'] == 'disabled':
        continue

    number = int(i.get('number'), 0)
    require = i.find('require')
    protect = i.get('protect')
    type_ = i.attrib['type']

    extension = None
    if protect:
        for j in platform_protects:
            if protect in platform_protects[j]:
                extension = platform_extensions[j]
                break
    else:
        extension = general_extensions

    assert not extension is None

    extension.update(i.attrib['name'] for i in require.findall('enum'))
    extension.update(i.attrib['name'] for i in require.findall('type'))
    extension.update(i.attrib['name'] for i in require.findall('command'))
    for i in require.findall('command'):
        extension_types[i.attrib['name']] = type_

    for j in require.findall('enum'):
        if 'extends' in j.attrib:
            assert j.attrib['extends'] in enums
            enums[j.attrib['extends']][j.attrib['name']] = evalEnum(j, number)
        else:
            macros[j.attrib['name']] = evalEnum(j)

for i in enums_ranges:
    enums[i].update(**enums_ranges[i])

all_extensions = reduce(lambda x, y: x.union(y), platform_extensions.values()).union(general_extensions)

def_orders = []

for i in struct_unions:
    def _(name):
        if name in def_orders:
            return
        __, members = struct_unions[name]
        for j, __, ___ in members:
            if j.endswith('*'):
                j = j[:-1]
            if j in struct_unions:
                _(j)
        def_orders.append(name)
    _(i)

assert len(struct_unions) == len(def_orders)
struct_unions = OrderedDict((k, struct_unions[k]) for k in def_orders)

funcs_return_list = set()
funcs_return_list_len_specified = set()
funcs_return_single = set()
funcs_return_nothing = set()
funcs_return_procaddr = set()
all_successcodes = set()
all_errorcodes = set()

funcs_len_autos = {}

for i in tree.findall('commands/command'):
    type_ = i.find('proto/type').text
    name = i.find('proto/name').text
    successcodes = i.get('successcodes')
    if successcodes:
        all_successcodes.update(successcodes.split(','))
    errorcodes = i.get('errorcodes')
    if errorcodes:
        all_errorcodes.update(errorcodes.split(','))
    params = i.findall('param')
    param_names = [j.find('name').text for j in params]

    value = (type_, name, [innertext(j).strip() for j in params], [(((j.text or '') + j.find('type').text + j.find('type').tail).strip(), j.find('name').text) for j in params])
    funcs[name] = value

    len_ = params[-1].get('len')
    if len_:
        lens = len_.split(',')
        assert len(lens) == 1
        if lens[0] == 'null-terminated':
            assert name in {'vkGetDeviceProcAddr', 'vkGetInstanceProcAddr'}
            params = params[:-1]
            funcs_return_procaddr.add(name)
        elif params[-1].text and params[-1].text.strip() == 'const':
            funcs_return_nothing.add(name)
        elif lens[0] in param_names:

            if params[-1].get('optional') != 'true':
                params = params[:-1]
                funcs_return_list_len_specified.add(name)
            else:
                assert lens[0] == param_names[-2]
                assert params[-1].find('type').tail.strip() == '*'
                params = params[:-2]
                funcs_return_list.add(name)
        else:
            assert name in ['vkAllocateDescriptorSets', 'vkAllocateCommandBuffers']
            params = params[:-1]
            funcs_return_list_len_specified.add(name)
    elif (params[-1].text is None or params[-1].text.strip() != 'const'):
        tail = params[-1].find('type').tail.strip()
        if tail == '*':
            if any(name.startswith(i) for i in {'vkGet', 'vkCreate', 'vkAllocate', 'vkAcquire'}):
                params = params[:-1]
                funcs_return_single.add(name)
            else:
                assert name in {'vkDebugMarkerSetObjectNameEXT', 'vkDebugMarkerSetObjectTagEXT', 'vkCmdDebugMarkerBeginEXT', 'vkCmdDebugMarkerInsertEXT'}
                funcs_return_nothing.add(name)
        elif tail == '**':
            assert name in {'vkMapMemory'}
            params = params[:-1]
            funcs_return_single.add(name)
        else:
            funcs_return_nothing.add(name)
    else:
        funcs_return_nothing.add(name)

    param_names = [j.find('name').text for j in params]

    funcs_len_autos[name] = {}
    for j in params:
        len_ = j.get('len')
        name_ = j.find('name').text
        if len_:
            lens = [i for i in len_.split(',') if i != 'null-terminated']
            if len(lens) == 1:
                if lens[0] in param_names:
                    if not lens[0] in funcs_len_autos[name]:
                        funcs_len_autos[name][lens[0]] = []
                    funcs_len_autos[name][lens[0]].append("len(%s)" % name_)
            else:
                assert not lens
            # print lens[0]

for i in funcs_len_autos:
    if funcs_len_autos[i]:
        pass
        # print i
        # assert funcs_return_single.intersection(funcs_return_list_len_specified)
assert not all_errorcodes.intersection(all_successcodes)
all_successcodes.remove('VK_SUCCESS')


def _(name):
    chunks = name.split('_')
    if name in all_extensions:
        return ''.join(i[0] + i[1:].lower() for i in chunks[:-1]) + chunks[-1]
    else:
        return ''.join(i[0] + i[1:].lower() for i in chunks)

exceptions = {i: _(i) for i in all_successcodes}
errors = {i: _(i) for i in all_errorcodes}
exception_codes = '{%s}' % ', '.join('%s:%s' % (i, _(i)) for i in all_successcodes.union(all_errorcodes))

constructors = {}
for i in struct_unions:
    _, fields = struct_unions[i]
    wrapper_params = ', '.join([("%s=%s" % (k, structs_default_values[i][k] if k in structs_default_values[i] else None)) for _, k, _ in fields])
    call_params = ', '.join("%s=%s" % (k, k) for _, k, _ in fields)
    len_autos = structs_len_autos[i].items()

    constructors[i] = (wrapper_params, call_params, len_autos)

throwable_funcs = set(k for k, v in funcs.items() if v == 'VkResult')

func_wrappers = {}
for name, (type_, _, _, params) in funcs.items():
    func_wrappers[name] = (type_, [i for i, _ in params], [i for _, i in params])

platform_vkapi_ptr = {'linux': '', 'win32': '__stdcall ', 'android': ''}
platform_newline = {'linux': '\n', 'win32': '\n', 'android': '\n'}

from jinja2 import *
import os
env = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))), trim_blocks=True)


instance_ext_funcs = [i for i in all_extensions if i in funcs and extension_types[i]=='instance']
device_ext_funcs = [i for i in all_extensions if i in funcs and extension_types[i]=='device']

genvulkan = env.get_template('vulkan.template.py')
with open('../pyVulkan/_vulkan.py', 'w') as f:
    f.write(genvulkan.render(len=len, **globals()))

genheader = env.get_template('header.template.h')
for i in platform_extensions:
    def _(x):
        return {j: x[j] for j in x if not j in all_extensions or j in platform_extensions[i] or j in general_extensions}
    with io.open('../pyVulkan/vulkan_%s_cffi.h' % i, 'w', newline=platform_newline[i]) as f:
        f.write(genheader.render(extensions=all_extensions, macros=macros, typedefs=_(typedefs), enums=_(enums), struct_unions=_(struct_unions), funcs=_(funcs), ext_funcs=_(ext_funcs), funcpointers=_(funcpointers), vkapi_ptr=platform_vkapi_ptr[i]))

gentestenum = env.get_template('testenum.template.c')
with io.open('/home/sobrans/sandbox/testenum.c', 'w', newline=platform_newline[i]) as f:
    f.write(gentestenum.render(enums=enums, macros=macros, extensions=all_extensions))
