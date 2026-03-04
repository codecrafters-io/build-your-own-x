import os
import shutil
import subprocess
import time
import ctypes

class SystemTools:
    def __init__(self):
        pass
    
    def delete_files(self, file_paths, force=False):
        """删除文件列表"""
        deleted = []
        failed = []
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                failed.append((file_path, 'File not found'))
                continue
            
            if not force:
                confirm = input(f'Are you sure you want to delete {file_path}? (y/n): ')
                if confirm.lower() != 'y':
                    failed.append((file_path, 'User cancelled'))
                    continue
            
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
                deleted.append(file_path)
                print(f'Deleted: {file_path}')
            except Exception as e:
                failed.append((file_path, str(e)))
                print(f'Failed to delete {file_path}: {e}')
        
        return {'deleted': deleted, 'failed': failed}
    
    def batch_delete_text_files(self, directory, force=False):
        """批量删除目录中的文本文件"""
        if not os.path.exists(directory):
            print(f'Directory not found: {directory}')
            return {'deleted': [], 'failed': []}
        
        text_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.txt'):
                    text_files.append(os.path.join(root, file))
        
        print(f'Found {len(text_files)} text files to delete')
        return self.delete_files(text_files, force)
    
    def shutdown_system(self, force=False, timeout=0):
        """关闭系统"""
        if not force:
            confirm = input('Are you sure you want to shutdown the system? (y/n): ')
            if confirm.lower() != 'y':
                print('Shutdown cancelled')
                return False
        
        if timeout > 0:
            print(f'System will shutdown in {timeout} seconds...')
            time.sleep(timeout)
        
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['shutdown', '/s', '/t', '0'], check=True)
            else:  # Unix-like
                subprocess.run(['shutdown', '-h', 'now'], check=True)
            return True
        except Exception as e:
            print(f'Error shutting down system: {e}')
            return False
    
    def restart_system(self, force=False, timeout=0):
        """重启系统"""
        if not force:
            confirm = input('Are you sure you want to restart the system? (y/n): ')
            if confirm.lower() != 'y':
                print('Restart cancelled')
                return False
        
        if timeout > 0:
            print(f'System will restart in {timeout} seconds...')
            time.sleep(timeout)
        
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['shutdown', '/r', '/t', '0'], check=True)
            else:  # Unix-like
                subprocess.run(['shutdown', '-r', 'now'], check=True)
            return True
        except Exception as e:
            print(f'Error restarting system: {e}')
            return False
