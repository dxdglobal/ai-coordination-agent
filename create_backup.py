#!/usr/bin/env python3

import os
import shutil
import datetime
import zipfile
import json

def create_comprehensive_backup():
    """
    Create multiple backup strategies for the AI coordination agent project
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_dir = f"../ai-coordination-agent-backup-{timestamp}"
    
    print("🔒 CREATING COMPREHENSIVE PROJECT BACKUP")
    print("=" * 60)
    print(f"📅 Timestamp: {timestamp}")
    print(f"📁 Backup Directory: {backup_dir}")
    
    # 1. Create backup directory
    print("\n📂 Creating backup directory...")
    try:
        os.makedirs(backup_dir, exist_ok=True)
        print(f"   ✅ Created: {backup_dir}")
    except Exception as e:
        print(f"   ❌ Error creating backup directory: {e}")
        return
    
    # 2. Copy entire project
    print("\n📋 Copying project files...")
    try:
        # Copy main project files
        for item in os.listdir('.'):
            if item.startswith('.git'):
                continue  # Skip .git directory for now
            
            source = item
            destination = os.path.join(backup_dir, item)
            
            if os.path.isdir(source):
                shutil.copytree(source, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'node_modules'))
                print(f"   ✅ Copied directory: {item}")
            else:
                shutil.copy2(source, destination)
                print(f"   ✅ Copied file: {item}")
    except Exception as e:
        print(f"   ❌ Error copying files: {e}")
    
    # 3. Create ZIP archive
    print("\n📦 Creating ZIP archive...")
    try:
        zip_filename = f"../ai-coordination-agent-backup-{timestamp}.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_dir):
                # Skip large or unnecessary directories
                dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules', '.git']]
                
                for file in files:
                    if not file.endswith(('.pyc', '.log', '.tmp')):
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_dir)
                        zipf.write(file_path, arcname)
        
        zip_size = os.path.getsize(zip_filename) / (1024 * 1024)  # Size in MB
        print(f"   ✅ Created ZIP: {zip_filename} ({zip_size:.2f} MB)")
    except Exception as e:
        print(f"   ❌ Error creating ZIP: {e}")
    
    # 4. Create git bundle backup
    print("\n🌿 Creating Git bundle backup...")
    try:
        bundle_filename = f"../ai-coordination-agent-git-{timestamp}.bundle"
        os.system(f'git bundle create "{bundle_filename}" --all')
        
        if os.path.exists(bundle_filename):
            bundle_size = os.path.getsize(bundle_filename) / (1024 * 1024)
            print(f"   ✅ Created Git bundle: {bundle_filename} ({bundle_size:.2f} MB)")
        else:
            print(f"   ❌ Git bundle creation failed")
    except Exception as e:
        print(f"   ❌ Error creating Git bundle: {e}")
    
    # 5. Create project manifest
    print("\n📋 Creating project manifest...")
    try:
        manifest = {
            "backup_info": {
                "timestamp": timestamp,
                "project_name": "AI Coordination Agent",
                "backup_type": "Comprehensive Backup",
                "git_commit": os.popen('git rev-parse HEAD').read().strip(),
                "git_branch": os.popen('git branch --show-current').read().strip()
            },
            "directories": [],
            "key_files": [],
            "environment_info": {
                "python_version": os.popen('python --version').read().strip(),
                "node_version": os.popen('node --version').read().strip() if shutil.which('node') else "Not installed",
                "os": os.name
            }
        }
        
        # Scan directories and files
        for root, dirs, files in os.walk('.'):
            # Skip hidden and cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
            
            relative_root = os.path.relpath(root, '.')
            if relative_root != '.':
                manifest["directories"].append(relative_root)
            
            for file in files:
                if file.endswith(('.py', '.js', '.jsx', '.json', '.md', '.bat', '.txt')):
                    file_path = os.path.join(relative_root, file) if relative_root != '.' else file
                    manifest["key_files"].append(file_path)
        
        # Save manifest
        manifest_path = os.path.join(backup_dir, "BACKUP_MANIFEST.json")
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ Created manifest: BACKUP_MANIFEST.json")
        print(f"      📁 Directories: {len(manifest['directories'])}")
        print(f"      📄 Key files: {len(manifest['key_files'])}")
        
    except Exception as e:
        print(f"   ❌ Error creating manifest: {e}")
    
    # 6. Create restore instructions
    print("\n📝 Creating restore instructions...")
    try:
        restore_instructions = f"""# AI Coordination Agent - Restore Instructions

## Backup Information
- **Created**: {timestamp}
- **Git Commit**: {os.popen('git rev-parse HEAD').read().strip()}
- **Git Branch**: {os.popen('git branch --show-current').read().strip()}

## Backup Contents
1. **Full Project Copy**: `{backup_dir}`
2. **ZIP Archive**: `ai-coordination-agent-backup-{timestamp}.zip`
3. **Git Bundle**: `ai-coordination-agent-git-{timestamp}.bundle`
4. **Project Manifest**: `BACKUP_MANIFEST.json`

## Restore Options

### Option 1: Restore from Directory Copy
```bash
# Copy the backup directory to desired location
cp -r "{backup_dir}" "ai-coordination-agent-restored"
cd ai-coordination-agent-restored
```

### Option 2: Restore from ZIP Archive
```bash
# Extract ZIP archive
unzip "ai-coordination-agent-backup-{timestamp}.zip" -d "ai-coordination-agent-restored"
cd ai-coordination-agent-restored
```

### Option 3: Restore Git Repository from Bundle
```bash
# Clone from git bundle
git clone "ai-coordination-agent-git-{timestamp}.bundle" "ai-coordination-agent-git-restored"
cd ai-coordination-agent-git-restored
```

## Setup After Restore

### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Set environment variables
export DB_PASSWORD='your_db_password'
export OPENAI_API_KEY='your_openai_key'

# Start backend
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## Important Notes
- Remember to set up environment variables (.env files)
- Update database credentials as needed
- Verify all API keys and sensitive configurations
- Check that all services are running correctly

## Emergency Contact
- If you need help restoring, refer to the BACKUP_MANIFEST.json for file structure
- All Python scripts for DDS AI online status fixes are included
- Database connection scripts use environment variables for security
"""
        
        restore_path = os.path.join(backup_dir, "RESTORE_INSTRUCTIONS.md")
        with open(restore_path, 'w', encoding='utf-8') as f:
            f.write(restore_instructions)
        
        print(f"   ✅ Created restore instructions: RESTORE_INSTRUCTIONS.md")
        
    except Exception as e:
        print(f"   ❌ Error creating restore instructions: {e}")
    
    # 7. Summary
    print("\n🎉 BACKUP COMPLETE!")
    print("=" * 60)
    print("📋 Backup Summary:")
    print(f"   📁 Full backup: {backup_dir}")
    print(f"   📦 ZIP archive: ai-coordination-agent-backup-{timestamp}.zip")
    print(f"   🌿 Git bundle: ai-coordination-agent-git-{timestamp}.bundle")
    print(f"   📋 Manifest: BACKUP_MANIFEST.json")
    print(f"   📝 Instructions: RESTORE_INSTRUCTIONS.md")
    print()
    print("💡 You now have multiple backup options:")
    print("   1. Complete directory copy (easiest to restore)")
    print("   2. Compressed ZIP archive (space efficient)")
    print("   3. Git bundle (preserves full git history)")
    print()
    print("🔒 Your AI Coordination Agent project is safely backed up!")

if __name__ == "__main__":
    create_comprehensive_backup()