import os
import subprocess
import uuid
from flask import request, jsonify
from flask_cors import CORS
from app import create_app
from .trace import extract_trace_py, extract_trace_coco

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
CORS(app)

@app.route('/coconut', methods=['POST'])
def coconut():
    """
    Handles Coconut code submitted by users.
    """
    code = request.form['code']

    # Write a code to a file with randomly generated filename.
    filename = str(uuid.uuid4())
    with open(filename, 'w') as output:
        output.write(code)

    # Initialize parameters
    output_text = ''
    compile_error = False
    running_error = False
    proc = None
    python_code = ''
    coconut_error_lines = []
    python_error_lines = []

    # Compile the user's code with Coconut compiler
    try:
        subprocess.run(["coconut", filename], stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as error:
        compile_error = True
        output_text = str(error.stderr, 'utf-8')
        print("Error in compiling Coconut's code")

    if compile_error:
        coconut_error_lines = extract_trace_coco(output_text)
    else:
        print("Finish compilation [{:}] to [{:}.py]".format(filename, filename))

        # Obtain coconut code.
        compiled_code = None
        with open(filename + ".py", "r") as compiled_file:
            compiled_code = compiled_file.read()

        SEPARATOR = "# Compiled Coconut: -----------------------------------------------------------\n\n"
        header, python_code = compiled_code.split(SEPARATOR)
        header_len = header.count('\n') + SEPARATOR.count('\n')

        # Run the compiled code.
        try:
            proc = subprocess.run(["python", filename + ".py"], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError as error:
            running_error = True
            output_text = str(error.stderr, 'utf-8')
            print("Error in running Coconut's code")

        if running_error:
            python_error_lines = extract_trace_py(output_text)
            # Offset line number by length of coconut header
            python_error_lines = [line_num-header_len for line_num in python_error_lines]
        else:
            # Store output from the run
            output_text = proc.stdout.decode('utf-8')
            print("Finish running [{:}]".format(filename + ".py"))

        # Remove temporary file that we compiled (*.py)
        subprocess.run(["rm", filename + '.py'])

    # Remove temporary file that stored the code
    subprocess.run(["rm", filename])
    print("Delete temp files {:} and {:}.py".format(filename, filename))

    # Print output
    print("Output is\n{:}".format(output_text))

    # Return JSON output
    return jsonify({'output': output_text,
                    'python': python_code,
                    'pythonErrorLines': python_error_lines,
                    'coconutErrorLines': coconut_error_lines})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
