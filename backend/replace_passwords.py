#!/usr/bin/env python3

import os
import re
import glob

def replace_hardcoded_passwords():
    """
    Replace hardcoded database passwords with environment variable references
    """
    print("🔒 REPLACING HARDCODED PASSWORDS WITH ENVIRONMENT VARIABLES")
    print("=" * 60)
    
    # Pattern to find hardcoded password (fix escaping)
    password_pattern = r"password\s*=\s*['\"]3@6\\\*t:lU['\"]"
    replacement = "password=os.environ.get('DB_PASSWORD', 'your_password_here')"
    
    # Also need to ensure os import is present
    os_import_pattern = r"^import os$"
    
    # Find all Python files in backend directory
    backend_files = glob.glob("backend/*.py")
    
    modified_files = []
    
    for file_path in backend_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file has hardcoded password
            if re.search(password_pattern, content):
                print(f"📝 Fixing: {file_path}")
                
                # Replace hardcoded password
                new_content = re.sub(password_pattern, replacement, content)
                
                # Check if 'import os' is already present
                if 'import os' not in new_content and 'os.environ' in new_content:
                    # Add import os at the top after other imports
                    lines = new_content.split('\n')
                    import_inserted = False
                    
                    for i, line in enumerate(lines):
                        if line.startswith('import ') or line.startswith('from '):
                            # Insert after the last import
                            if i + 1 < len(lines) and not (lines[i + 1].startswith('import ') or lines[i + 1].startswith('from ')):
                                lines.insert(i + 1, 'import os')
                                import_inserted = True
                                break
                    
                    if not import_inserted:
                        # Insert at the beginning if no imports found
                        lines.insert(0, 'import os')
                    
                    new_content = '\n'.join(lines)
                
                # Write back the modified content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                modified_files.append(file_path)
        
        except Exception as e:
            print(f"⚠️  Error processing {file_path}: {e}")
    
    print(f"\n✅ Modified {len(modified_files)} files:")
    for file_path in modified_files:
        print(f"   - {file_path}")
    
    print(f"\n💡 Don't forget to set the DB_PASSWORD environment variable!")
    print(f"   export DB_PASSWORD='3@6*t:lU'")

if __name__ == "__main__":
    replace_hardcoded_passwords()