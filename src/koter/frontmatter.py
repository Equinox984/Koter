"""Manejo de frontmatter YAML compatible con Obsidian."""

import re
from pathlib import Path


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parsea el frontmatter YAML de una nota.
    Devuelve (metadata, contenido_sin_frontmatter).
    """
    lines = content.split('\n')
    
    # Buscar delimitadores ---
    if not lines or lines[0].strip() != '---':
        return {}, content
    
    # Buscar el segundo ---
    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_idx = i
            break
    
    if end_idx == -1:
        return {}, content
    
    # Extraer YAML
    yaml_lines = lines[1:end_idx]
    body = '\n'.join(lines[end_idx + 1:])
    
    # Parsear YAML manualmente (sin dependencias)
    metadata = {}
    current_key = None
    current_list = []
    
    for line in yaml_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        
        # Lista en curso
        if stripped.startswith('- ') and current_key:
            current_list.append(stripped[2:].strip())
            continue
        
        # Guardar lista si existe
        if current_key and current_list and not stripped.startswith('- '):
            metadata[current_key] = current_list
            current_list = []
            current_key = None
        
        # Par clave: valor
        match = re.match(r'^(\w+):\s*(.*)$', stripped)
        if match:
            key, value = match.groups()
            current_key = key
            
            # Booleano
            if value.lower() == 'true':
                metadata[key] = True
                current_key = None
            elif value.lower() == 'false':
                metadata[key] = False
                current_key = None
            # Lista inline [a, b]
            elif value.startswith('[') and value.endswith(']'):
                items = value[1:-1].split(',')
                metadata[key] = [item.strip() for item in items if item.strip()]
                current_key = None
            # String vacío o valor simple
            elif value:
                metadata[key] = value.strip()
            # Lista en líneas siguientes
            else:
                current_list = []
    
    # Guardar última lista si existe
    if current_key and current_list:
        metadata[current_key] = current_list
    
    return metadata, body.strip()


def build_frontmatter(metadata: dict) -> str:
    """Construye el frontmatter YAML desde un diccionario."""
    lines = ['---']
    
    for key, value in metadata.items():
        if isinstance(value, bool):
            lines.append(f"{key}: {str(value).lower()}")
        elif isinstance(value, list):
            if len(value) == 0:
                lines.append(f"{key}: []")
            elif len(value) <= 3:
                # Formato inline para listas cortas
                items = ', '.join(f'"{v}"' if ',' in v or ' ' in v else v for v in value)
                lines.append(f"{key}: [{items}]")
            else:
                # Formato multilínea
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    
    lines.append('---')
    return '\n'.join(lines)


def update_note_content(path: Path, title: str, content: str, 
                        tags: list[str] = None, pinned: bool = False,
                        created: str = None, modified: str = None) -> None:
    """
    Actualiza o crea una nota con frontmatter.
    Si el archivo existe, preserva el contenido y actualiza metadata.
    """
    tags = tags or []
    
    # Leer existente si hay
    if path.exists():
        existing_meta, existing_content = parse_frontmatter(path.read_text())
        # Preservar valores existentes si no se proporcionan nuevos
        if created is None:
            created = existing_meta.get('created', created)
        content_to_save = content if content else existing_content
    else:
        content_to_save = content
    
    metadata = {
        'title': title,
        'created': created or '',
        'modified': modified or '',
        'tags': tags,
        'pinned': pinned
    }
    
    frontmatter = build_frontmatter(metadata)
    full_content = f"{frontmatter}\n\n{content_to_save}"
    
    path.write_text(full_content)


def get_note_metadata(path: Path) -> dict:
    """Obtiene solo la metadata de una nota."""
    if not path.exists():
        return {}
    content = path.read_text()
    metadata, _ = parse_frontmatter(content)
    return metadata
