from pathlib import Path

# Generate the trajectory file
values = [
    (4.0, 4.0),
    (1.0, 1.0),
    (5.0, 5.0),
    (0.0, 0.0),
    (3.0, 3.0),
]

lines = []

for v1, v2 in values:
    for _ in range(600):
        lines.append(f"{v1:.1f} {v2:.1f}")

content = "\n".join(lines)

# Save in the current folder
output_path = Path("trajetoria_setpoints.txt")

output_path.write_text(content, encoding="utf-8")

print(f"Arquivo gerado com {len(lines)} linhas.")
print(f"Caminho: {output_path.resolve()}")