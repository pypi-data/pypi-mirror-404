# document_notebook.py
import os
import nbformat
import time
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    project="proj_SC2qCbCTE3AVzqw1pRTRlqCg"
)

INPUT_PATH = "app/model_testing/4_CatBoostClassifier_weekly.ipynb"
OUTPUT_PATH = INPUT_PATH.replace(".ipynb", "_doc.ipynb")  # Guardar como _doc

# Load the notebook
nb = nbformat.read(INPUT_PATH, as_version=4)

prompt = """
You are a code reviewer and documentation expert. For every code cell below:
- Add a docstring if the cell contains a function.
- Add inline comments explaining what each step does.
- If it plots something, describe the purpose of the plot.
- Only explain; do not change any logic.

Return only the improved version of the code.
"""

# Loop through code cells
for cell in nb.cells:
    if cell.cell_type == "code":
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": cell.source}
                ],
                temperature=0
            )
            cell.source = response.choices[0].message.content
            time.sleep(1.5)
        except Exception as e:
            print(f"❌ Error processing cell: {e}")
            continue

# Save updated notebook
nbformat.write(nb, OUTPUT_PATH)
print(f"Documented notebook saved to: {OUTPUT_PATH}")