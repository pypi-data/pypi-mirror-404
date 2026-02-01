import os
from jinja2 import Environment, FileSystemLoader

def render_template(templates_dir, template, context, output_path, output_template) -> None:
    env = Environment(loader=FileSystemLoader(templates_dir))
    t = os.path.join(output_path, output_template)

    os.makedirs(output_path, exist_ok=True)

    try:
        template = env.get_template(template)
        render_context = template.render(context)

        with open(t, mode='w', newline='\n') as f:
            f.write(render_context)
        print(f"OK: Generated: {output_path}")
    except Exception as e:
        print(f"Error: Failed to render {template}: {e}")