import subprocess
import time
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

def run_my_process(cmds):
    print(f"cmds: {cmds}")
    try:
        process = subprocess.Popen(
            cmds,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
    except Exception as e:
        print(e)
    try:
        while True:
            line = process.stderr.readline()
            if line == "" and process.poll() is not None:
                break
            print(line, end="")
    finally:
        process.stdout.close()

        
def convert_to_tikz(data):
    tikz_code = []
    custom_colors = {}
    color_index = {}  # 用于跟踪颜色定义顺序
    canvas_height = 400  # 假设画布高度为 400 像素

    for shape in data.get('objects', []):
        if shape['type'] == 'circle':
            center_x = shape['left'] + shape['radius']
            center_y = canvas_height - (shape['top'] + shape['radius'])  # 修正Y坐标
            radius = shape['radius']
            color = shape.get('fill', '')
            if color:
                if color not in color_index:
                    color_index[color] = f"color{len(color_index) + 1}"
                    custom_colors[color_index[color]] = color
                tikz_code.append(
                    f"\\draw[fill={color_index[color]}] ({center_x / 100}, {center_y / 100}) circle ({radius / 100});")
            else:
                tikz_code.append(f"\\draw ({center_x / 100}, {center_y / 100}) circle ({radius / 100});")

        elif shape['type'] == 'rect':
            left_x = shape['left'] / 100
            left_y = canvas_height - shape['top'] / 100
            width = shape['width'] / 100
            height = shape['height'] / 100
            color = shape.get('fill', '')
            if color:
                if color not in color_index:
                    color_index[color] = f"color{len(color_index) + 1}"
                    custom_colors[color_index[color]] = color
                tikz_code.append(
                    f"\\draw[fill={color_index[color]}] ({left_x}, {left_y}) rectangle ({left_x + width}, {left_y - height});")
            else:
                tikz_code.append(f"\\draw ({left_x}, {left_y}) rectangle ({left_x + width}, {left_y - height});")

        elif shape['type'] == 'line':
            x1, y1 = shape['x1'] / 100, canvas_height - shape['y1'] / 100
            x2, y2 = shape['x2'] / 100, canvas_height - shape['y2'] / 100
            color = shape.get('stroke', '')
            if color:
                if color not in color_index:
                    color_index[color] = f"color{len(color_index) + 1}"
                    custom_colors[color_index[color]] = color
                tikz_code.append(f"\\draw[{color_index[color]}] ({x1}, {y1}) -- ({x2}, {y2});")
            else:
                tikz_code.append(f"\\draw ({x1}, {y1}) -- ({x2}, {y2});")

    # Add color definitions if custom colors are used
    if data.get('useCustomColor') and custom_colors:
        color_definitions = ["\\usepackage{xcolor} % Required for color definitions"]
        for name, hex_code in custom_colors.items():
            color_definitions.append(f"\\definecolor{{{name}}}{{HTML}}{{{hex_code.lstrip('#')}}}")
        tikz_code = color_definitions + tikz_code

    return '\n'.join(tikz_code)


@app.route('/api/generate-tikz', methods=['POST'])
def generate_tikz():
    data = request.json

    tikz_code = convert_to_tikz(data)

    response = {
        'tikzCode': tikz_code
    }

    return jsonify(response)


@app.route('/api/generate-graphic', methods=['POST'])
def generate_graphic():
    data = request.json

    tikz_code = data['tikz_code']

    loca=time.strftime('%Y-%m-%d_%H-%M-%S')
    tex_name = str(loca) + ".tex"
    tex_path = os.path.join('cache\\tex', tex_name)

    with open(tex_path, 'w', encoding='utf-8') as file:
        file.write(tikz_code)

    cmd = 'xelatex -output-directory=cache/pdf cache/tex/' + tex_name
    code = os.system(cmd)

    if not code:
        pdf_name = str(loca) + ".pdf"
        pdf_path = os.path.join('cache\\pdf', pdf_name)

        return send_file(pdf_path)

    return send_file('msg\\compile_error.pdf')


if __name__ == '__main__':
    app.run(debug=True)
