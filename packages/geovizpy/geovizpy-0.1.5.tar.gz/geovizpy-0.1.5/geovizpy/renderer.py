"""Module for rendering the map to HTML and JSON."""

import json
import tempfile
import os
import time

class RendererMixin:
    """Mixin class for rendering the map."""

    def get_config(self):
        """Return the configuration as a JSON-compatible list of commands."""
        def process_args(args):
            new_args = {}
            for k, v in args.items():
                if v is None:
                    continue
                if isinstance(v, str) and (v.strip().startswith("(") or v.strip().startswith("function") or "=>" in v):
                     new_args[k] = {"__js_func__": v}
                elif isinstance(v, dict):
                    new_args[k] = process_args(v)
                else:
                    new_args[k] = v
            return new_args

        processed_commands = []
        for cmd in self.commands:
            processed_commands.append({"name": cmd["name"], "args": process_args(cmd["args"])})
        
        return processed_commands

    def to_json(self):
        """Return the configuration as a JSON string."""
        return json.dumps(self.get_config())

    def render_html(self, filename="map.html"):
        """Render the map to an HTML file."""
        json_commands = self.to_json()
        
        layer_control_js = self._get_layer_control_js()
        export_control_js = self._get_export_control_js()

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
  <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Tangerine"/>
  <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
  <script src="https://cdn.jsdelivr.net/npm/geoviz@0.9.8"></script>
  <style>
    body {{ margin: 0; padding: 0; }}
    button {{ background: #f8f9fa; border: 1px solid #ddd; border-radius: 3px; }}
    button:hover {{ background: #e2e6ea; }}
  </style>
</head>
<body>
<script>
  const commands = {json_commands};
  let svg;

  // Helper to revive functions
  function revive(obj) {{
    if (typeof obj === 'object' && obj !== null) {{
      if (obj.hasOwnProperty('__js_func__')) {{
         try {{
            return eval(obj['__js_func__']);
         }} catch (e) {{
            console.error("Failed to eval function:", obj['__js_func__'], e);
            return null;
         }}
      }} else {{
         for (let key in obj) {{
            obj[key] = revive(obj[key]);
         }}
      }}
    }}
    return obj;
  }}

  const revivedCommands = revive(commands);

  revivedCommands.forEach(cmd => {{
    if (cmd.name === "create") {{
      svg = geoviz.create(cmd.args);
    }} else {{
      const parts = cmd.name.split(".");
      if (parts.length === 1) {{
         if (svg[parts[0]]) {{
            svg[parts[0]](cmd.args);
         }} else {{
            console.warn("Method " + parts[0] + " not found");
         }}
      }} else if (parts.length === 2) {{
         if (svg[parts[0]] && svg[parts[0]][parts[1]]) {{
            svg[parts[0]][parts[1]](cmd.args);
         }} else {{
            console.warn("Method " + cmd.name + " not found");
         }}
      }}
    }}
  }});

  if (svg) {{
    document.body.appendChild(svg.render());
  }}
  
  {layer_control_js}
  {export_control_js}
</script>
</body>
</html>
"""
        with open(filename, "w") as f:
            f.write(html_content)
        print(f"Map saved to {filename}")

    def save(self, filename="map.html"):
        """
        Save the map to a file.
        
        If filename ends with .html, saves the interactive map.
        If filename ends with .png or .svg, saves a static image.
        
        For image export, 'playwright' is required. Install it with:
        pip install geovizpy[export]
        playwright install
        """
        if filename.endswith(".html"):
            self.render_html(filename)
        elif filename.endswith(".png") or filename.endswith(".svg"):
            self._save_image(filename)
        else:
            print("Error: filename must end with .html, .png, or .svg")

    def _save_image(self, filename):
        """Internal method to save as PNG or SVG using Playwright."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("Error: Playwright is required for image export.")
            print("Please install it with: pip install geovizpy[export] && playwright install")
            return

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as tmp_file:
            self.render_html(tmp_file.name)
            tmp_path = tmp_file.name

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": 1000, "height": 800})
                page.goto(f"file://{os.path.abspath(tmp_path)}")
                page.wait_for_timeout(2000)

                if filename.endswith(".svg"):
                    svg_outer = page.locator("svg").first.evaluate("el => el.outerHTML")
                    with open(filename, "w") as f:
                        f.write(svg_outer)
                else: # .png
                    page.locator("svg").first.screenshot(path=filename)
                
                browser.close()
                print(f"Image saved to {filename}")
        except Exception as e:
            print(f"Error saving image: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _get_layer_control_js(self):
        if not self.layer_control_config:
            return ""
        config = self.layer_control_config
        layers_json = json.dumps(config["layers"]) if config["layers"] else "null"
        return f"""
            const layerConfig = {{
                layers: {layers_json},
                pos: "{config.get('pos')}",
                x: {config.get('x', 10)},
                y: {config.get('y', 10)},
                title: "{config.get('title', 'Layers')}"
            }};
            
            function createLayerControl() {{
                const wrapper = document.createElement("div");
                wrapper.style.position = "absolute";
                wrapper.style.zIndex = "1000";
                
                const button = document.createElement("div");
                button.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="#333"><path d="M11.99 18.54l-7.37-5.73L3 14.07l9 7 9-7-1.63-1.27-7.38 5.74zM12 16l7.36-5.73L21 9l-9-7-9 7 1.63 1.27L12 16z"/></svg>`;
                button.style.width = "32px";
                button.style.height = "32px";
                button.style.cursor = "pointer";
                button.style.border = "1px solid #ccc";
                button.style.borderRadius = "4px";
                button.style.backgroundColor = "white";
                button.style.display = "flex";
                button.style.alignItems = "center";
                button.style.justifyContent = "center";
                button.style.boxShadow = "0 1px 3px rgba(0,0,0,0.2)";
                
                const panel = document.createElement("div");
                panel.style.display = "none";
                panel.style.backgroundColor = "white";
                panel.style.padding = "10px";
                panel.style.border = "1px solid #ccc";
                panel.style.borderRadius = "5px";
                panel.style.fontFamily = "sans-serif";
                panel.style.fontSize = "12px";
                panel.style.boxShadow = "0 2px 4px rgba(0,0,0,0.2)";
                panel.style.marginTop = "5px";
                panel.style.minWidth = "100px";

                wrapper.addEventListener("mouseenter", () => panel.style.display = "block");
                wrapper.addEventListener("mouseleave", () => panel.style.display = "none");

                if (layerConfig.pos === "top-right") {{
                    wrapper.style.top = "10px"; wrapper.style.right = "10px";
                }} else if (layerConfig.pos === "bottom-right") {{
                    wrapper.style.bottom = "10px"; wrapper.style.right = "10px";
                }} else if (layerConfig.pos === "bottom-left") {{
                    wrapper.style.bottom = "10px"; wrapper.style.left = "10px";
                }} else {{
                    wrapper.style.top = `${{layerConfig.y}}px`;
                    wrapper.style.left = `${{layerConfig.x}}px`;
                }}
                
                const title = document.createElement("div");
                title.innerText = layerConfig.title;
                title.style.fontWeight = "bold";
                title.style.marginBottom = "8px";
                title.style.borderBottom = "1px solid #eee";
                title.style.paddingBottom = "5px";
                panel.appendChild(title);

                let layers = layerConfig.layers;
                if (!layers) {{
                    layers = Array.from(svg.selectAll("g[id]").nodes()).map(n => n.id);
                }}

                let count = 0;
                layers.forEach(layerId => {{
                    const layer = svg.select("#" + layerId);
                    if (!layer.empty()) {{
                        count++;
                        const row = document.createElement("div");
                        row.style.marginBottom = "5px";
                        row.style.display = "flex";
                        row.style.alignItems = "center";
                        
                        const checkbox = document.createElement("input");
                        checkbox.type = "checkbox";
                        checkbox.id = "chk_" + layerId;
                        checkbox.checked = true;
                        checkbox.style.marginRight = "8px";
                        checkbox.style.cursor = "pointer";
                        
                        checkbox.addEventListener("change", (e) => {{
                            const display = e.target.checked ? "inline" : "none";
                            layer.style("display", display);
                            const legLayer = svg.select("#leg_" + layerId);
                            if (!legLayer.empty()) legLayer.style("display", display);
                        }});
                        
                        const label = document.createElement("label");
                        label.htmlFor = "chk_" + layerId;
                        label.innerText = layerId;
                        label.style.cursor = "pointer";
                        
                        row.appendChild(checkbox);
                        row.appendChild(label);
                        panel.appendChild(row);
                    }}
                }});
                
                if (count > 0) {{
                    wrapper.appendChild(button);
                    wrapper.appendChild(panel);
                    document.body.appendChild(wrapper);
                }}
            }}
            setTimeout(createLayerControl, 100);
        """

    def _get_export_control_js(self):
        if not self.export_control_config:
            return ""
        ex_config = self.export_control_config
        return f"""
            const exportConfig = {{
                pos: "{ex_config.get('pos')}",
                x: {ex_config.get('x', 10)},
                y: {ex_config.get('y', 50)},
                title: "{ex_config.get('title', 'Export')}"
            }};

            function createExportControl() {{
                const wrapper = document.createElement("div");
                wrapper.style.position = "absolute";
                wrapper.style.zIndex = "1000";

                const button = document.createElement("div");
                button.innerHTML = `<svg width="24" height="24" viewBox="0 0 24 24" fill="#333"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>`;
                button.style.width = "32px";
                button.style.height = "32px";
                button.style.cursor = "pointer";
                button.style.border = "1px solid #ccc";
                button.style.borderRadius = "4px";
                button.style.backgroundColor = "white";
                button.style.display = "flex";
                button.style.alignItems = "center";
                button.style.justifyContent = "center";
                button.style.boxShadow = "0 1px 3px rgba(0,0,0,0.2)";

                const panel = document.createElement("div");
                panel.style.display = "none";
                panel.style.backgroundColor = "white";
                panel.style.padding = "5px";
                panel.style.border = "1px solid #ccc";
                panel.style.borderRadius = "5px";
                panel.style.marginTop = "5px";
                panel.style.boxShadow = "0 2px 4px rgba(0,0,0,0.2)";
                panel.style.display = "none";
                panel.style.flexDirection = "column";
                panel.style.gap = "5px";

                wrapper.addEventListener("mouseenter", () => panel.style.display = "flex");
                wrapper.addEventListener("mouseleave", () => panel.style.display = "none");

                if (exportConfig.pos === "top-right") {{
                    wrapper.style.top = "50px"; wrapper.style.right = "10px";
                }} else if (exportConfig.pos === "bottom-right") {{
                    wrapper.style.bottom = "50px"; wrapper.style.right = "10px";
                }} else {{
                    wrapper.style.top = `${{exportConfig.y}}px`;
                    wrapper.style.left = `${{exportConfig.x}}px`;
                }}

                const btnSVG = document.createElement("button");
                btnSVG.innerText = "SVG";
                btnSVG.style.cursor = "pointer";
                btnSVG.style.padding = "5px 10px";
                btnSVG.onclick = () => {{
                    geoviz.exportSVG(svg, {{filename: "map.svg"}});
                }};

                const btnPNG = document.createElement("button");
                btnPNG.innerText = "PNG";
                btnPNG.style.cursor = "pointer";
                btnPNG.style.padding = "5px 10px";
                btnPNG.onclick = () => {{
                    geoviz.exportPNG(svg, {{filename: "map.png"}});
                }};

                panel.appendChild(btnSVG);
                panel.appendChild(btnPNG);
                wrapper.appendChild(button);
                wrapper.appendChild(panel);
                document.body.appendChild(wrapper);
            }}
            setTimeout(createExportControl, 100);
        """
