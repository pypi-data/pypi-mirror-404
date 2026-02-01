# coding: utf-8


from dataclasses import dataclass
import requests
import os

current_dir = os.path.dirname(os.path.abspath(__file__))


@dataclass
class Brick:
    name: str
    description: str = ''
    content: str = ''


    @classmethod
    def from_local(cls, name: str) -> 'Brick':
        brick_file = os.path.join(current_dir, 'bricks', name)
        if not os.path.exists(brick_file):
            raise FileNotFoundError(f'Brick file {brick_file} not found')
        with open(brick_file, 'r') as f:
            content = f.read()
            try:
                description = content.split('"""')[1].split('"""')[0]
            except Exception:
                description = ''
        return cls(name=name, content=content, description=description)

    @classmethod
    def from_remote(cls, name: str) -> 'Brick':
        remote_url = f"https://public-xmov.oss-cn-hangzhou.aliyuncs.com/tmp/code/{name}"
        response = requests.get(remote_url)
        if response.status_code != 200:
            raise Exception(f'Failed to get brick from remote: {response.status_code}')
        content = response.text
        description = content.split('"""')[1].split('"""')[0]
        return cls(name=name, content=content, description=description)
    
    @classmethod
    def from_name(cls, name: str) -> 'Brick':
        try:
            return cls.from_local(name)
        except FileNotFoundError:
            try:
                return cls.from_remote(name)
            except Exception:
                print(f'ERROR: Brick {name} not found')
                return cls(name=name)


    def create_file(self, dest_file_path:str = None):
        if dest_file_path is None:
            dest_file_path = self.name
        
        dir_path = os.path.dirname(dest_file_path)
        if len(dir_path) > 0 and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        with open(dest_file_path, 'w') as f:
            f.write(self.content)
        return dest_file_path