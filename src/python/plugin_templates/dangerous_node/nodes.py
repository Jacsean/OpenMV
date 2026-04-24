"""
危险测试插件 - 包含应被拦截的危险操作
"""

import os
import subprocess
from NodeGraphQt import BaseNode


class DangerousNode(BaseNode):
    """危险节点示例"""
    __identifier__ = 'test'
    NODE_NAME = '危险节点'
    
    def __init__(self):
        super(DangerousNode, self).__init__()
        self.add_input('输入')
        self.add_output('输出')
    
    def process(self, inputs=None):
        # 危险操作：执行系统命令
        os.system('echo "This is dangerous!"')
        
        # 危险操作：启动子进程
        subprocess.call(['ls', '-la'])
        
        return {'输出': None}
