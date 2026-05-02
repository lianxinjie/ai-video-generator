#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
场景查看器和编辑器

功能：
1. 显示场景切分结果
2. 支持用户查看和修改场景
3. 导出为 JSON 配置文件
4. 支持从配置文件导入
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class SceneViewer:
    """场景查看器"""
    
    def __init__(self, verbose: bool = True):
        """
        初始化场景查看器
        
        Args:
            verbose: 是否显示详细信息
        """
        self.verbose = verbose
        self.scenes: List[Dict] = []
    
    def load_scenes(self, scenes: List[Dict]):
        """加载场景列表"""
        self.scenes = scenes
        
        if self.verbose:
            print(f"\n✓ 已加载 {len(scenes)} 个场景")
    
    def display_scenes(self, show_details: bool = True):
        """
        显示场景列表
        
        Args:
            show_details: 是否显示详细信息
        """
        if not self.scenes:
            print("  暂无场景数据")
            return
        
        print("\n" + "="*70)
        print(f"  场景列表（共 {len(self.scenes)} 个场景）")
        print("="*70)
        
        total_duration = 0
        
        for i, scene in enumerate(self.scenes, 1):
            duration = scene.get('duration', 0)
            total_duration += duration
            
            print(f"\n【场景 {i:02d}】时长：{duration:.1f}秒")
            
            # 显示提示词
            prompt = scene.get('prompt', '')
            if prompt:
                print(f"  提示词：{prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            
            # 显示详细信息
            if show_details:
                # 参考图
                if scene.get('reference_images'):
                    ref_count = len(scene['reference_images'])
                    print(f"  参考图：{ref_count} 张")
                
                # 配音
                if scene.get('voiceover'):
                    vo = scene['voiceover']
                    print(f"  配音：{vo.get('text', '')[:50]}")
                    print(f"       语音：{vo.get('voice', 'N/A')}, "
                          f"情绪：{vo.get('emotion', 'N/A')}")
                
                # 场景类型
                if scene.get('scene_type'):
                    print(f"  类型：{scene['scene_type']}")
                
                # 生成位置
                if scene.get('generation_location'):
                    print(f"  生成位置：{scene['generation_location']}")
        
        print("\n" + "="*70)
        print(f"  总时长：{total_duration:.1f}秒")
        print("="*70)
    
    def export_to_json(self, output_file: str) -> bool:
        """
        导出场景到 JSON 文件
        
        Args:
            output_file: 输出文件路径
        
        Returns:
            是否成功
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'total_scenes': len(self.scenes),
                'total_duration': sum(s.get('duration', 0) for s in self.scenes),
                'scenes': self.scenes
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            if self.verbose:
                print(f"\n✓ 场景已导出到：{output_file}")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"\n✗ 导出失败：{e}")
            return False
    
    def import_from_json(self, input_file: str) -> bool:
        """
        从 JSON 文件导入场景
        
        Args:
            input_file: 输入文件路径
        
        Returns:
            是否成功
        """
        try:
            input_path = Path(input_file)
            
            if not input_path.exists():
                if self.verbose:
                    print(f"✗ 文件不存在：{input_file}")
                return False
            
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.scenes = data.get('scenes', [])
            
            if self.verbose:
                print(f"\n✓ 已从 {input_file} 导入 {len(self.scenes)} 个场景")
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"\n✗ 导入失败：{e}")
            return False


class SceneEditor:
    """场景编辑器（交互式）"""
    
    def __init__(self, scenes: List[Dict], verbose: bool = True):
        """
        初始化场景编辑器
        
        Args:
            scenes: 场景列表
            verbose: 是否显示详细信息
        """
        self.scenes = scenes
        self.verbose = verbose
        self.modified = False
    
    def edit_scene(self, scene_index: int, **kwargs) -> bool:
        """
        编辑指定场景
        
        Args:
            scene_index: 场景索引（从 1 开始）
            **kwargs: 要修改的字段
        
        Returns:
            是否成功
        """
        if scene_index < 1 or scene_index > len(self.scenes):
            if self.verbose:
                print(f"✗ 无效的场景索引：{scene_index}")
            return False
        
        scene = self.scenes[scene_index - 1]
        
        # 更新字段
        for key, value in kwargs.items():
            if key in scene:
                old_value = scene[key]
                scene[key] = value
                
                if self.verbose:
                    print(f"  ✓ 场景{scene_index} 的 [{key}] 已更新")
                    print(f"    原值：{old_value}")
                    print(f"    新值：{value}")
            else:
                if self.verbose:
                    print(f"  ⚠ 场景{scene_index} 不存在字段 [{key}]")
        
        self.modified = True
        return True
    
    def add_scene(self, position: int, scene_data: Dict) -> bool:
        """
        添加新场景
        
        Args:
            position: 插入位置（从 1 开始）
            scene_data: 场景数据
        
        Returns:
            是否成功
        """
        if position < 1 or position > len(self.scenes) + 1:
            if self.verbose:
                print(f"✗ 无效的位置：{position}")
            return False
        
        self.scenes.insert(position - 1, scene_data)
        self.modified = True
        
        if self.verbose:
            print(f"  ✓ 已在新位置 {position} 添加场景")
        
        return True
    
    def delete_scene(self, scene_index: int) -> bool:
        """
        删除场景
        
        Args:
            scene_index: 场景索引（从 1 开始）
        
        Returns:
            是否成功
        """
        if scene_index < 1 or scene_index > len(self.scenes):
            if self.verbose:
                print(f"✗ 无效的场景索引：{scene_index}")
            return False
        
        deleted = self.scenes.pop(scene_index - 1)
        self.modified = True
        
        if self.verbose:
            print(f"  ✓ 已删除场景 {scene_index}")
        
        return True
    
    def get_scenes(self) -> List[Dict]:
        """获取场景列表"""
        return self.scenes
    
    def is_modified(self) -> bool:
        """是否已修改"""
        return self.modified


def interactive_edit_menu(scenes: List[Dict]) -> List[Dict]:
    """
    交互式编辑菜单
    
    Args:
        scenes: 场景列表
    
    Returns:
        修改后的场景列表
    """
    print("\n" + "="*70)
    print("  场景编辑器 - 交互式菜单")
    print("="*70)
    print("\n可用命令:")
    print("  view         - 查看所有场景")
    print("  edit <编号>  - 编辑指定场景")
    print("  add <位置>   - 添加新场景")
    print("  delete <编号>- 删除场景")
    print("  export <文件> - 导出到 JSON")
    print("  import <文件> - 从 JSON 导入")
    print("  done         - 完成编辑")
    print("  quit         - 退出（不保存）")
    print("="*70)
    
    viewer = SceneViewer(verbose=True)
    viewer.load_scenes(scenes)
    
    editor = SceneEditor(scenes, verbose=True)
    
    while True:
        try:
            cmd = input("\n请输入命令 > ").strip().split()
            
            if not cmd:
                continue
            
            command = cmd[0].lower()
            
            if command == 'view':
                viewer.display_scenes(show_details=True)
            
            elif command == 'edit':
                if len(cmd) < 2:
                    print("  用法：edit <场景编号>")
                    continue
                
                scene_idx = int(cmd[1])
                
                # 简单编辑：只修改提示词和时长
                print(f"\n编辑场景 {scene_idx}:")
                new_prompt = input(f"  提示词 [{viewer.scenes[scene_idx-1].get('prompt', '')}]: ").strip()
                new_duration = input(f"  时长 [{viewer.scenes[scene_idx-1].get('duration', 0)}]: ").strip()
                
                updates = {}
                if new_prompt:
                    updates['prompt'] = new_prompt
                if new_duration:
                    updates['duration'] = float(new_duration)
                
                editor.edit_scene(scene_idx, **updates)
            
            elif command == 'add':
                if len(cmd) < 2:
                    print("  用法：add <位置>")
                    continue
                
                position = int(cmd[1])
                
                print(f"\n在位置 {position} 添加新场景:")
                prompt = input("  提示词：").strip()
                duration = input("  时长（秒）:").strip()
                
                new_scene = {
                    'prompt': prompt,
                    'duration': float(duration) if duration else 5.0,
                    'scene_type': 'default',
                    'generation_location': 'local'
                }
                
                editor.add_scene(position, new_scene)
            
            elif command == 'delete':
                if len(cmd) < 2:
                    print("  用法：delete <场景编号>")
                    continue
                
                scene_idx = int(cmd[1])
                confirm = input(f"  确认删除场景 {scene_idx}? (y/n): ").strip().lower()
                
                if confirm == 'y':
                    editor.delete_scene(scene_idx)
            
            elif command == 'export':
                if len(cmd) < 2:
                    print("  用法：export <文件名>")
                    continue
                
                filename = cmd[1]
                viewer.scenes = editor.get_scenes()
                viewer.export_to_json(filename)
            
            elif command == 'import':
                if len(cmd) < 2:
                    print("  用法：import <文件名>")
                    continue
                
                filename = cmd[1]
                if viewer.import_from_json(filename):
                    editor.scenes = viewer.scenes
                    editor.modified = True
            
            elif command == 'done':
                if editor.is_modified():
                    confirm = input("  保存修改？(y/n): ").strip().lower()
                    if confirm == 'y':
                        print("  ✓ 修改已保存")
                        return editor.get_scenes()
                    else:
                        print("  ⚠ 修改未保存")
                        return scenes
                else:
                    print("  无修改")
                    return scenes
            
            elif command == 'quit':
                if editor.is_modified():
                    confirm = input("  有未保存的修改，确定退出？(y/n): ").strip().lower()
                    if confirm == 'y':
                        print("  ⚠ 修改已丢弃")
                        return scenes
                else:
                    return scenes
            
            else:
                print(f"  未知命令：{command}")
                print("  输入 'help' 查看可用命令")
        
        except KeyboardInterrupt:
            print("\n\n  ⚠ 编辑中断")
            return scenes
        
        except Exception as e:
            print(f"\n  ✗ 错误：{e}")


def test_scene_viewer():
    """测试场景查看器"""
    print("="*70)
    print("场景查看器和编辑器测试")
    print("="*70)
    
    # 测试数据
    test_scenes = [
        {
            'id': 1,
            'prompt': '一个勇敢的骑士站在古老城堡前，准备迎接挑战',
            'duration': 5.0,
            'scene_type': 'character',
            'generation_location': 'local',
            'reference_images': ['char_001.png']
        },
        {
            'id': 2,
            'prompt': '城堡内部，华丽的王座大厅，阳光透过彩色玻璃',
            'duration': 4.5,
            'scene_type': 'background',
            'generation_location': 'cloud',
            'reference_images': ['bg_001.png']
        },
        {
            'id': 3,
            'prompt': '激烈的战斗场面，骑士与巨龙在天空中飞舞',
            'duration': 6.0,
            'scene_type': 'action',
            'generation_location': 'local',
            'voiceover': {
                'text': '勇敢的骑士挥舞着他的宝剑',
                'voice': 'zh-CN-XiaoxiaoNeural',
                'emotion': 'excited'
            }
        }
    ]
    
    # 测试查看器
    viewer = SceneViewer(verbose=True)
    viewer.load_scenes(test_scenes)
    viewer.display_scenes(show_details=True)
    
    # 测试导出
    test_output = '/tmp/test_scenes.json'
    viewer.export_to_json(test_output)
    
    # 测试导入
    viewer2 = SceneViewer(verbose=True)
    viewer2.import_from_json(test_output)
    viewer2.display_scenes(show_details=False)
    
    print("\n✓ 所有测试完成")


if __name__ == "__main__":
    test_scene_viewer()
