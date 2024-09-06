import time
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS, cross_origin
import os

app = Flask(__name__)
CORS(app)

# 设置缩放比例，缩小10倍
SCALE_FACTOR = 0.05

# 生成 TikZ 代码的主函数
# 生成 TikZ 代码的主函数
def generate_tikz_code(drawing_data):
    tikz_code = []
    # 添加 LaTeX 文档的头部
    tikz_code.append(r"\documentclass{article}")
    tikz_code.append(r"\usepackage{tikz}")
    tikz_code.append(r"\begin{document}")
    tikz_code.append(r"\begin{tikzpicture}")

    # 遍历画布中的每个对象，生成 TikZ 代码
    for obj in drawing_data['objects']:
        label = obj.get('label', None)
        if label:
            tikz_code.append(convert_object_to_tikz(obj, drawing_data['useCustomColor']))
        else:
            print(f"Warning: Missing 'label' in object {obj}. Skipping this object.")

    # 处理点与线之间的关系，根据 objectRelationMap 来生成对应的 TikZ 代码
    tikz_code += generate_relation_tikz(drawing_data['objectRelationMap'])

    tikz_code.append(r"\end{tikzpicture}")
    tikz_code.append(r"\end{document}")  # 添加 LaTeX 文档的结尾
    return "\n".join(tikz_code)

# 处理关系映射，生成相关 TikZ 代码
def generate_relation_tikz(relation_map):
    tikz_lines = []
    for relation_name, relation_info in relation_map.items():
        relation_type = relation_info['type']
        nodes = relation_info['selectionNodes']

        # 检查 selectionNodes 是否为空
        if not nodes:
            continue

        # 根据不同类型处理
        if relation_type == 'Node':
            tikz_lines += [draw_node_from_selection(node) for node in nodes]
        elif relation_type == 'Straight Line':
            tikz_lines.append(draw_straight_line_from_nodes(nodes))
        elif relation_type == 'Broken Line':
            tikz_lines.append(draw_broken_line_from_nodes(nodes))
        elif relation_type == 'Curve':
            tikz_lines.append(draw_curve_from_nodes(nodes))
        elif relation_type == 'Circle':
            for node in nodes:
                if 'left' in node and 'top' in node and 'radius' in node:
                    tikz_lines.append(draw_circle_from_selection(node))
        elif relation_type == 'Rectangle':
            if len(nodes) == 2:
                tikz_lines.append(draw_rectangle_from_selection(nodes))
        elif relation_type == 'Customize Graphics':  # 处理多边形
            tikz_lines.append(draw_polygon_from_selection(nodes))
    return tikz_lines

# 画布对象到 TikZ 代码的转换函数
def convert_object_to_tikz(obj, use_custom_color):
    tikz_lines = []
    label = obj.get('label', '') or obj.get('type', '')

    # 根据对象类型生成 TikZ 代码
    if label == 'Node':
        tikz_lines.append(draw_node(obj, use_custom_color))
    elif label == 'Straight Line':
        line_code = draw_straight_line(obj, use_custom_color)
        if line_code:
            tikz_lines.append(line_code)
    elif label == 'Broken Line':
        line_code = draw_broken_line(obj, use_custom_color)
        if line_code:
            tikz_lines.append(line_code)
    elif label == 'Curve':
        curve_code = draw_curve(obj, use_custom_color)
        if curve_code:
            tikz_lines.append(curve_code)
    elif label == 'Circle' or obj.get('type') == 'circle':
        # Use draw_circle_from_selection for circles
        if 'left' in obj and 'top' in obj and 'radius' in obj:
            tikz_lines.append(draw_circle_from_selection(obj))  # Correct function for circles
    elif label == 'Rectangle':
        # Use draw_rectangle_from_selection for rectangles if two points are defined
        if 'left' in obj and 'top' in obj:  # Adjust this condition based on actual object structure
            tikz_lines.append(draw_rectangle_from_selection([obj]))  # Use the selection method directly
    elif label == 'Customize Graphics':
        custom_code = draw_custom_graphics(obj, use_custom_color)
        if custom_code:
            tikz_lines.append(custom_code)
    else:
        print(f"Warning: Missing 'label' in object {obj}. Skipping this object.")

    return "\n".join([line for line in tikz_lines if line.strip()])


# 各种图形的 TikZ 代码生成函数
def draw_node(obj, use_custom_color):
    color = obj.get('fill', 'black') if use_custom_color else 'black'
    x, y = obj['left'] * SCALE_FACTOR, -obj['top'] * SCALE_FACTOR
    return f"\\node at ({x:.2f}, {y:.2f}) {{}};"

# 从 selectionNodes 中提取节点并生成 TikZ 代码
def draw_node_from_selection(node):
    x, y = node['left'] * SCALE_FACTOR, -node['top'] * SCALE_FACTOR
    return f"\\node at ({x:.2f}, {y:.2f}) {{}};"

# 处理关系中的圆形节点
def draw_circle_from_selection(node):
    x, y = node['left'] * SCALE_FACTOR, -node['top'] * SCALE_FACTOR
    radius = node['radius'] * SCALE_FACTOR
    return f"\\draw ({x:.2f}, {y:.2f}) circle [radius={radius:.2f}cm];"

# 处理关系中的矩形节点
def draw_rectangle_from_selection(nodes):
    top_left = nodes[0]
    bottom_right = nodes[1]
    x1, y1 = top_left['left'] * SCALE_FACTOR, -top_left['top'] * SCALE_FACTOR
    x2, y2 = bottom_right['left'] * SCALE_FACTOR, -bottom_right['top'] * SCALE_FACTOR
    return f"\\draw ({x1:.2f}, {y1:.2f}) rectangle ({x2:.2f}, {y2:.2f});"

# 处理关系中的多边形节点
def draw_polygon_from_selection(nodes):
    # 获取每个顶点的坐标
    points = [(node['left'] * SCALE_FACTOR, -node['top'] * SCALE_FACTOR) for node in nodes]
    # 生成 TikZ 的绘图路径
    path = " -- ".join([f"({x:.2f}, {y:.2f})" for x, y in points])
    # 闭合路径，形成多边形
    return f"\\draw {path} -- cycle;"

def draw_straight_line(obj, use_custom_color):
    color = obj.get('stroke', 'black') if use_custom_color else 'black'
    x1, y1 = obj['x1'] * SCALE_FACTOR, -obj['y1'] * SCALE_FACTOR
    x2, y2 = obj['x2'] * SCALE_FACTOR, -obj['y2'] * SCALE_FACTOR
    return f"\\draw[{color}] ({x1:.2f}, {y1:.2f}) -- ({x2:.2f}, {y2:.2f});"

def draw_broken_line(obj, use_custom_color):
    color = obj.get('stroke', 'black') if use_custom_color else 'black'
    points = [(p['x'] * SCALE_FACTOR, -p['y'] * SCALE_FACTOR) for p in obj['points']]
    path = " -- ".join([f"({x:.2f}, {y:.2f})" for x, y in points])
    return f"\\draw[{color}] {path};"

def draw_curve(obj, use_custom_color):
    color = obj.get('stroke', 'black') if use_custom_color else 'black'
    points = [(p['x'] * SCALE_FACTOR, -p['y'] * SCALE_FACTOR) for p in obj['points']]
    path = " ".join([f"({x:.2f}, {y:.2f})" for x, y in points])
    return f"\\draw plot[smooth, tension=.7] coordinates {{{path}}};"

def draw_custom_graphics(obj, use_custom_color):
    color = obj.get('fill', 'black') if use_custom_color else 'black'
    points = [(p['x'] * SCALE_FACTOR, -p['y'] * SCALE_FACTOR) for p in obj['points']]
    path = " -- ".join([f"({x:.2f}, {y:.2f})" for x, y in points])
    return f"\\fill[{color}] {path} -- cycle;"

# 根据节点绘制直线
def draw_straight_line_from_nodes(nodes):
    coords = [(node['left'] * SCALE_FACTOR, -node['top'] * SCALE_FACTOR) for node in nodes]
    path = " -- ".join([f"({x:.2f}, {y:.2f})" for x, y in coords])
    return f"\\draw {path};"

# 根据节点绘制折线
def draw_broken_line_from_nodes(nodes):
    coords = [(node['left'] * SCALE_FACTOR, -node['top'] * SCALE_FACTOR) for node in nodes]
    path = " -- ".join([f"({x:.2f}, {y:.2f})" for x, y in coords])
    return f"\\draw {path};"

# 根据节点绘制曲线
def draw_curve_from_nodes(nodes):
    coords = [(node['left'] * SCALE_FACTOR, -node['top'] * SCALE_FACTOR) for node in nodes]
    path = " ".join([f"({x:.2f}, {y:.2f})" for x, y in coords])
    return f"\\draw plot[smooth, tension=.7] coordinates {{{path}}};"

# 接收前端数据并返回 TikZ 代码
@app.route('/api/generate-tikz', methods=['POST'])
@cross_origin()
def generate_tikz():
    drawing_data = request.json
    tikz_code = generate_tikz_code(drawing_data)
    return jsonify({'tikzCode': tikz_code})

@app.route('/api/generate-graphic', methods=['POST'])
@cross_origin()
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
    app.run(host="0.0.0.0",port=8090)
