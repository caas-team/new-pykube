import code

import pykube

config = pykube.KubeConfig.from_file()
print(f'KubeConfig: {config.filename}, current context: {config.current_context}')
api = pykube.HTTPClient(config)

context = {
    '__name__': '__console__',
    'pykube': pykube,
    'config': config,
    'api': api
}
for k, v in vars(pykube).items():
    if k[0] != '_' and k[0] == k[0].upper():
        context[k] = v

console = code.InteractiveConsole(locals=context)
console.interact(f'Pykube v{pykube.__version__}\nUse Ctrl-D to exit\n{", ".join(sorted(context.keys()))}')
