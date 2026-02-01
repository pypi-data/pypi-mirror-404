import hashlib

class RuntimeManager:
    def __init__(self):
        self.running_modules = {}
        self.compat_mode = False

    def get_code_fingerprint(self, source):
        fingerprint = hashlib.md5(source.encode('utf-8')).hexdigest()
        print(f"🔍 生成代码指纹：{fingerprint[:8]}...")
        return fingerprint

    def start_monitor(self, module_name, source):
        fingerprint = self.get_code_fingerprint(source)
        self.running_modules[module_name] = {
            'fingerprint': fingerprint,
            'status': 'running'
        }
        print(f"📋 启动监控：{module_name}")

    def stop_monitor(self, module_name):
        if module_name in self.running_modules:
            del self.running_modules[module_name]
            print(f"🛑 停止监控：{module_name}")

cycy_runtime = RuntimeManager()