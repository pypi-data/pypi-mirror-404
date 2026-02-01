import re

def formatter(source, language, css_class, options, md, classes, id_value, attrs=None, **kwargs):
    opt=''
    # Set default height to 150px if not provided in options
    if "height" not in options.keys():
        opt+=f' style="height: 150px;"'

    for x,y in options.items():
        if x=='height':
            opt+= f' style="height: {y}px;"'
        else:
            opt+= f' {x}="{y}"'
    pattern = r'^\s*:\w+:\s*\w+.*$'
    source = re.sub(pattern, '', source, flags=re.MULTILINE)
    template=f"""<logic-editor exportformat="superfence" {opt}>
    <script type="application/json">
        {source}
    </script>
    </logic-editor>"""
    return template
  
def validator(language, inputs, options, attrs, md):
    """Custom validator."""
    okay = True
    for k, v in inputs.items():
        options[k] = v
    return okay
