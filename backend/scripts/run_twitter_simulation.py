"""
OASIS Twitter Simulation Preset Script
This script reads parameters from a configuration file to execute simulations automatically.

Features:
- Does not immediately close environment after simulation; enters wait-for-command mode.
- Supports receiving Interview commands via IPC.
- Supports single Agent and batch Agent interviews.
- Supports remote environment closure commands.

Usage:
    python run_twitter_simulation.py --config /path/to/simulation_config.json
    python run_twitter_simulation.py --config /path/to/simulation_config.json --no-wait  # Close immediately after completion
"""

import argparse
import asyncio
import json
import logging
import os
import random
import signal
import sys
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

# 全局变量：用于信号处理
_shutdown_event = None
_cleanup_done = False

# 添加项目路径
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.abspath(os.path.join(_scripts_dir, '..'))
_project_root = os.path.abspath(os.path.join(_backend_dir, '..'))
sys.path.insert(0, _scripts_dir)
sys.path.insert(0, _backend_dir)

# 加载项目根目录的 .env 文件（包含 LLM_API_KEY 等配置）
from dotenv import load_dotenv
_env_file = os.path.join(_project_root, '.env')
if os.path.exists(_env_file):
    load_dotenv(_env_file)
else:
    _backend_env = os.path.join(_backend_dir, '.env')
    if os.path.exists(_backend_env):
        load_dotenv(_backend_env)


import re


class UnicodeFormatter(logging.Formatter):
    """自定义格式化器，将 Unicode 转义序列转换为可读字符"""
    
    UNICODE_ESCAPE_PATTERN = re.compile(r'\\u([0-9a-fA-F]{4})')
    
    def format(self, record):
        result = super().format(record)
        
        def replace_unicode(match):
            try:
                return chr(int(match.group(1), 16))
            except (ValueError, OverflowError):
                return match.group(0)
        
        return self.UNICODE_ESCAPE_PATTERN.sub(replace_unicode, result)


class MaxTokensWarningFilter(logging.Filter):
    """过滤掉 camel-ai 关于 max_tokens 的警告（我们故意不设置 max_tokens，让模型自行决定）"""
    
    def filter(self, record):
        # 过滤掉包含 max_tokens 警告的日志
        if "max_tokens" in record.getMessage() and "Invalid or missing" in record.getMessage():
            return False
        return True


# 在模块加载时立即添加过滤器，确保在 camel 代码执行前生效
logging.getLogger().addFilter(MaxTokensWarningFilter())


def setup_oasis_logging(log_dir: str):
    """配置 OASIS 的日志，使用固定名称的日志文件"""
    os.makedirs(log_dir, exist_ok=True)
    
    # 清理旧的日志文件
    for f in os.listdir(log_dir):
        old_log = os.path.join(log_dir, f)
        if os.path.isfile(old_log) and f.endswith('.log'):
            try:
                os.remove(old_log)
            except OSError:
                pass
    
    formatter = UnicodeFormatter("%(levelname)s - %(asctime)s - %(name)s - %(message)s")
    
    loggers_config = {
        "social.agent": os.path.join(log_dir, "social.agent.log"),
        "social.twitter": os.path.join(log_dir, "social.twitter.log"),
        "social.rec": os.path.join(log_dir, "social.rec.log"),
        "oasis.env": os.path.join(log_dir, "oasis.env.log"),
        "table": os.path.join(log_dir, "table.log"),
    }
    
    for logger_name, log_file in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()
        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.propagate = False


# Conditional imports for robust DEMO_MODE
try:
    from camel.models import ModelFactory
    from camel.types import ModelPlatformType
    import oasis
    from oasis.core.action import LLMAction, ManualAction, ActionType
except Exception as e:
    print(f"Warning: AI dependencies unavailable ({e}).")
    print("Running in limited mode. (Only valid if DEMO_MODE=True)")
    
    # Fallback for ActionType if oasis fails to load
    class ActionTypeFallBack:
        CREATE_POST = "CREATE_POST"
        LIKE_POST = "LIKE_POST"
        REPOST = "REPOST"
        FOLLOW = "FOLLOW"
        QUOTE_POST = "QUOTE_POST"
        DISLIKE_POST = "DISLIKE_POST"
        CREATE_COMMENT = "CREATE_COMMENT"
        LIKE_COMMENT = "LIKE_COMMENT"
        DISLIKE_COMMENT = "DISLIKE_COMMENT"
        SEARCH_POSTS = "SEARCH_POSTS"
        SEARCH_USER = "SEARCH_USER"
        TREND = "TREND"
        REFRESH = "REFRESH"
        DO_NOTHING = "DO_NOTHING"
    
    if 'ActionType' not in globals():
        ActionType = ActionTypeFallBack


def generate_synthetic_actions(
    round_num: int,
    simulated_hour: int,
    platform: str,
    agent_names: Dict[int, str],
    action_logger: Any,
    limit: int = 3
) -> int:
    """Generate realistic tech-themed synthetic actions for DEMO_MODE"""
    import random
    
    actions_pool = {
        "twitter": [
            ("CREATE_POST", "Analyzing swarm intelligence latency. Optimization required."),
            ("LIKE_POST", ""),
            ("REPLY", "Agreed. Nexus protocols are showing improved stability."),
            ("FOLLOW", ""),
            ("QUOTE_POST", "Check out these new throughput metrics. #OmniAgent"),
        ],
        "reddit": [
            ("CREATE_POST", "Discussion: Best practices for multi-agent graph anchoring."),
            ("LIKE_POST", ""),
            ("REPLY", "The ontology layer definitely helps with cross-agent coherence."),
            ("DISLIKE_POST", ""),
            ("CREATE_COMMENT", "Nexus v3 is a major step forward in UI glassmorphism."),
        ]
    }
    
    count = 0
    agent_ids = list(agent_names.keys())
    if not agent_ids:
        return 0
        
    # Each round, 1-N agents do something
    active_count = random.randint(1, min(len(agent_ids), limit))
    selected_agents = random.sample(agent_ids, active_count)
    
    for agent_id in selected_agents:
        action_type, content = random.choice(actions_pool.get(platform, actions_pool["twitter"]))
        
        action_args = {}
        if content:
            action_args["content"] = content
        
        # Add target IDs for variety
        if "post" in action_type.lower():
            action_args["post_id"] = random.randint(100, 999)
        if "comment" in action_type.lower():
            action_args["comment_id"] = random.randint(100, 999)
        if action_type == "FOLLOW":
            target_ids = [i for i in agent_ids if i != agent_id]
            if target_ids:
                target_id = random.choice(target_ids)
                action_args["target_id"] = target_id
                action_args["target_user_name"] = agent_names.get(target_id, f"Agent_{target_id}")
            
        action_logger.log_action(
            round_num=round_num,
            agent_id=agent_id,
            agent_name=agent_names.get(agent_id, f"Agent_{agent_id}"),
            action_type=action_type,
            action_args=action_args
        )
        count += 1
        
    return count


# IPC相关常量
IPC_COMMANDS_DIR = "ipc_commands"
IPC_RESPONSES_DIR = "ipc_responses"
ENV_STATUS_FILE = "env_status.json"

class CommandType:
    """Command Type Constants"""
    INTERVIEW = "interview"
    BATCH_INTERVIEW = "batch_interview"
    CLOSE_ENV = "close_env"


class IPCHandler:
    """IPC Command Handler"""
    
    def __init__(self, simulation_dir: str, env, agent_graph):
        self.simulation_dir = simulation_dir
        self.env = env
        self.agent_graph = agent_graph
        self.commands_dir = os.path.join(simulation_dir, IPC_COMMANDS_DIR)
        self.responses_dir = os.path.join(simulation_dir, IPC_RESPONSES_DIR)
        self.status_file = os.path.join(simulation_dir, ENV_STATUS_FILE)
        self._running = True
        
        # 确保目录存在
        os.makedirs(self.commands_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)
    
    def update_status(self, status: str):
        """Update environment status"""
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": status,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def poll_command(self) -> Optional[Dict[str, Any]]:
        """轮询获取待处理命令"""
        if not os.path.exists(self.commands_dir):
            return None
        
        # 获取命令文件（按时间排序）
        command_files = []
        for filename in os.listdir(self.commands_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.commands_dir, filename)
                command_files.append((filepath, os.path.getmtime(filepath)))
        
        command_files.sort(key=lambda x: x[1])
        
        for filepath, _ in command_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
        
        return None
    
    def send_response(self, command_id: str, status: str, result: Dict = None, error: str = None):
        """发送响应"""
        response = {
            "command_id": command_id,
            "status": status,
            "result": result,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        response_file = os.path.join(self.responses_dir, f"{command_id}.json")
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=2)
        
        # 删除命令文件
        command_file = os.path.join(self.commands_dir, f"{command_id}.json")
        try:
            os.remove(command_file)
        except OSError:
            pass
    
    async def handle_interview(self, command_id: str, agent_id: int, prompt: str) -> bool:
        """
        处理单个Agent采访命令
        
        Returns:
            True 表示成功，False 表示失败
        """
        try:
            # 获取Agent
            agent = self.agent_graph.get_agent(agent_id)
            
            # 创建Interview动作
            interview_action = ManualAction(
                action_type=ActionType.INTERVIEW,
                action_args={"prompt": prompt}
            )
            
            # 执行Interview
            actions = {agent: interview_action}
            await self.env.step(actions)
            
            # 从数据库获取结果
            result = self._get_interview_result(agent_id)
            
            self.send_response(command_id, "completed", result=result)
            print(f"  Interview完成: agent_id={agent_id}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"  Interview失败: agent_id={agent_id}, error={error_msg}")
            self.send_response(command_id, "failed", error=error_msg)
            return False
    
    async def handle_batch_interview(self, command_id: str, interviews: List[Dict]) -> bool:
        """
        处理批量采访命令
        
        Args:
            interviews: [{"agent_id": int, "prompt": str}, ...]
        """
        try:
            # 构建动作字典
            actions = {}
            agent_prompts = {}  # 记录每个agent的prompt
            
            for interview in interviews:
                agent_id = interview.get("agent_id")
                prompt = interview.get("prompt", "")
                
                try:
                    agent = self.agent_graph.get_agent(agent_id)
                    actions[agent] = ManualAction(
                        action_type=ActionType.INTERVIEW,
                        action_args={"prompt": prompt}
                    )
                    agent_prompts[agent_id] = prompt
                except Exception as e:
                    print(f"  警告: 无法获取Agent {agent_id}: {e}")
            
            if not actions:
                self.send_response(command_id, "failed", error="没有有效的Agent")
                return False
            
            # 执行批量Interview
            await self.env.step(actions)
            
            # 获取所有结果
            results = {}
            for agent_id in agent_prompts.keys():
                result = self._get_interview_result(agent_id)
                results[agent_id] = result
            
            self.send_response(command_id, "completed", result={
                "interviews_count": len(results),
                "results": results
            })
            print(f"  批量Interview完成: {len(results)} 个Agent")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"  批量Interview失败: {error_msg}")
            self.send_response(command_id, "failed", error=error_msg)
            return False
    
    def _get_interview_result(self, agent_id: int) -> Dict[str, Any]:
        """从数据库获取最新的Interview结果"""
        db_path = os.path.join(self.simulation_dir, "twitter_simulation.db")
        
        result = {
            "agent_id": agent_id,
            "response": None,
            "timestamp": None
        }
        
        if not os.path.exists(db_path):
            return result
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查询最新的Interview记录
            cursor.execute("""
                SELECT user_id, info, created_at
                FROM trace
                WHERE action = ? AND user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (ActionType.INTERVIEW.value, agent_id))
            
            row = cursor.fetchone()
            if row:
                user_id, info_json, created_at = row
                try:
                    info = json.loads(info_json) if info_json else {}
                    result["response"] = info.get("response", info)
                    result["timestamp"] = created_at
                except json.JSONDecodeError:
                    result["response"] = info_json
            
            conn.close()
            
        except Exception as e:
            print(f"  读取Interview结果失败: {e}")
        
        return result
    
    async def process_commands(self) -> bool:
        """
        处理所有待处理命令
        
        Returns:
            True 表示继续运行，False 表示应该退出
        """
        command = self.poll_command()
        if not command:
            return True
        
        command_id = command.get("command_id")
        command_type = command.get("command_type")
        args = command.get("args", {})
        
        print(f"\nReceived IPC command: {command_type}, id={command_id}")
        
        if command_type == CommandType.INTERVIEW:
            await self.handle_interview(
                command_id,
                args.get("agent_id", 0),
                args.get("prompt", "")
            )
            return True
            
        elif command_type == CommandType.BATCH_INTERVIEW:
            await self.handle_batch_interview(
                command_id,
                args.get("interviews", [])
            )
            return True
            
        elif command_type == CommandType.CLOSE_ENV:
            print("收到关闭环境命令")
            self.send_response(command_id, "completed", result={"message": "环境即将关闭"})
            return False
        
        else:
            self.send_response(command_id, "failed", error=f"Unknown command type: {command_type}")
            return True


class TwitterSimulationRunner:
    """Twitter Simulation Runner"""
    
    # Twitter可用动作（不包含INTERVIEW，INTERVIEW只能通过ManualAction手动触发）
    AVAILABLE_ACTIONS = [
        ActionType.CREATE_POST,
        ActionType.LIKE_POST,
        ActionType.REPOST,
        ActionType.FOLLOW,
        ActionType.DO_NOTHING,
        ActionType.QUOTE_POST,
    ]
    
    def __init__(self, config_path: str, wait_for_commands: bool = True):
        """
        初始化模拟运行器
        
        Args:
            config_path: 配置文件路径 (simulation_config.json)
            wait_for_commands: 模拟完成后是否等待命令（默认True）
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.simulation_dir = os.path.dirname(config_path)
        self.wait_for_commands = wait_for_commands
        self.env = None
        self.agent_graph = None
        self.ipc_handler = None
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_profile_path(self) -> str:
        """获取Profile文件路径（OASIS Twitter使用CSV格式）"""
        return os.path.join(self.simulation_dir, "twitter_profiles.csv")
    
    def _get_db_path(self) -> str:
        """获取数据库路径"""
        return os.path.join(self.simulation_dir, "twitter_simulation.db")
    
    def _create_model(self):
        """
        创建LLM模型
        
        统一使用项目根目录 .env 文件中的配置（优先级最高）：
        - LLM_API_KEY: API密钥
        - LLM_BASE_URL: API基础URL
        - LLM_MODEL_NAME: 模型名称
        """
        # 优先从 .env 读取配置
        llm_api_key = os.environ.get("LLM_API_KEY", "")
        llm_base_url = os.environ.get("LLM_BASE_URL", "")
        llm_model = os.environ.get("LLM_MODEL_NAME", "")
        
        # 如果 .env 中没有，则使用 config 作为备用
        if not llm_model:
            llm_model = self.config.get("llm_model", "gpt-4o-mini")
        
        # 设置 camel-ai 所需的环境变量
        if llm_api_key:
            os.environ["OPENAI_API_KEY"] = llm_api_key
        
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("缺少 API Key 配置，请在项目根目录 .env 文件中设置 LLM_API_KEY")
        
        if llm_base_url:
            os.environ["OPENAI_API_BASE_URL"] = llm_base_url
        
        print(f"LLM配置: model={llm_model}, base_url={llm_base_url[:40] if llm_base_url else '默认'}...")
        
        return ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=llm_model,
        )
    
    def _get_active_agents_for_round(
        self, 
        env, 
        current_hour: int,
        round_num: int
    ) -> List:
        """
        根据时间和配置决定本轮激活哪些Agent
        
        Args:
            env: OASIS环境
            current_hour: 当前模拟小时（0-23）
            round_num: 当前轮数
            
        Returns:
            激活的Agent列表
        """
        time_config = self.config.get("time_config", {})
        agent_configs = self.config.get("agent_configs", [])
        
        # 基础激活数量
        base_min = time_config.get("agents_per_hour_min", 5)
        base_max = time_config.get("agents_per_hour_max", 20)
        
        # 根据时段调整
        peak_hours = time_config.get("peak_hours", [9, 10, 11, 14, 15, 20, 21, 22])
        off_peak_hours = time_config.get("off_peak_hours", [0, 1, 2, 3, 4, 5])
        
        if current_hour in peak_hours:
            multiplier = time_config.get("peak_activity_multiplier", 1.5)
        elif current_hour in off_peak_hours:
            multiplier = time_config.get("off_peak_activity_multiplier", 0.3)
        else:
            multiplier = 1.0
        
        target_count = int(random.uniform(base_min, base_max) * multiplier)
        
        # 根据每个Agent的配置计算激活概率
        candidates = []
        for cfg in agent_configs:
            agent_id = cfg.get("agent_id", 0)
            active_hours = cfg.get("active_hours", list(range(8, 23)))
            activity_level = cfg.get("activity_level", 0.5)
            
            # 检查是否在活跃时间
            if current_hour not in active_hours:
                continue
            
            # 根据活跃度计算概率
            if random.random() < activity_level:
                candidates.append(agent_id)
        
        # 随机选择
        selected_ids = random.sample(
            candidates, 
            min(target_count, len(candidates))
        ) if candidates else []
        
        # 转换为Agent对象
        active_agents = []
        for agent_id in selected_ids:
            try:
                agent = env.agent_graph.get_agent(agent_id)
                active_agents.append((agent_id, agent))
            except Exception:
                pass
        
        return active_agents
    
        # Check if demo mode is enabled
        demo_mode = os.environ.get("DEMO_MODE", "False").lower() == "true"
        
        print("=" * 60)
        print("OASIS Twitter Simulation")
        print(f"Config File: {self.config_path}")
        print(f"Simulation ID: {self.config.get('simulation_id', 'unknown')}")
        print(f"Wait Mode: {'Enabled' if self.wait_for_commands else 'Disabled'}")
        if demo_mode:
            print("MODE: DEMO_MODE (Synthetic Generation Enabled)")
        print("=" * 60)
        
        # Load time config
        time_config = self.config.get("time_config", {})
        total_hours = time_config.get("total_simulation_hours", 72)
        minutes_per_round = time_config.get("minutes_per_round", 30)
        
        # Calculate total rounds
        total_rounds = (total_hours * 60) // minutes_per_round
        
        # Truncate if max_rounds specified
        if max_rounds is not None and max_rounds > 0:
            original_rounds = total_rounds
            total_rounds = min(total_rounds, max_rounds)
            if total_rounds < original_rounds:
                print(f"\nRounds truncated: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")
        
        print(f"\nSimulation Parameters:")
        print(f"  - Total Duration: {total_hours} hours")
        print(f"  - Time per Round: {minutes_per_round} minutes")
        print(f"  - Total Rounds: {total_rounds}")
        if max_rounds:
            print(f"  - Max Round Limit: {max_rounds}")
        print(f"  - Agent Count: {len(self.config.get('agent_configs', []))}")
        
        # Create model if not in demo mode
        if not demo_mode:
            print("\nInitializing LLM model...")
            model = self._create_model()
            
            # Load Agent graph
            print("Loading Agent Profiles...")
            profile_path = self._get_profile_path()
            if not os.path.exists(profile_path):
                print(f"Error: Profile file not found: {profile_path}")
                return
            
            self.agent_graph = await generate_twitter_agent_graph(
                profile_path=profile_path,
                model=model,
                available_actions=self.AVAILABLE_ACTIONS,
            )
            
            # Database path
            db_path = self._get_db_path()
            if os.path.exists(db_path):
                os.remove(db_path)
                print(f"Deleted old database: {db_path}")
            
            # Create environment
            print("Creating OASIS environment...")
            self.env = oasis.make(
                agent_graph=self.agent_graph,
                platform=oasis.DefaultPlatformType.TWITTER,
                database_path=db_path,
                semaphore=30,
            )
            
            await self.env.reset()
            print("Environment initialization complete\n")
        else:
            print("\nDEMO_MODE: Skipping heavy OASIS initialization.")
            print("Synthetic actions will be generated and logged.")
        
        # Initialize IPC handler
        self.ipc_handler = IPCHandler(self.simulation_dir, self.env, self.agent_graph)
        self.ipc_handler.update_status("running")
        
        # Execute initial events
        event_config = self.config.get("event_config", {})
        initial_posts = event_config.get("initial_posts", [])
        
        if initial_posts:
            print(f"Executing initial events ({len(initial_posts)} initial posts)...")
            initial_actions = {}
            for post in initial_posts:
                agent_id = post.get("poster_agent_id", 0)
                content = post.get("content", "")
                try:
                    agent = self.env.agent_graph.get_agent(agent_id)
                    initial_actions[agent] = ManualAction(
                        action_type=ActionType.CREATE_POST,
                        action_args={"content": content}
                    )
                except Exception as e:
                    if not demo_mode:
                        print(f"  Warning: Could not create initial post for Agent {agent_id}: {e}")
            
            if initial_actions or (demo_mode and initial_posts):
                if not demo_mode:
                    await self.env.step(initial_actions)
                print(f"  Published {len(initial_posts)} initial posts")
        
        # Main simulation loop
        print("\nStarting simulation loop...")
        start_time = datetime.now()
        for round_num in range(total_rounds):
            # Calculate current simulation time
            simulated_minutes = round_num * minutes_per_round
            simulated_hour = (simulated_minutes // 60) % 24
            simulated_day = simulated_minutes // (60 * 24) + 1
            
            # Check for exit signal
            if _shutdown_event and _shutdown_event.is_set():
                print(f"\nReceived exit signal, stopping at round {round_num + 1}")
                break
                
            if demo_mode:
                # Generate synthetic actions for demo
                round_action_count = generate_synthetic_actions(
                    round_num=round_num + 1,
                    simulated_hour=simulated_hour,
                    platform="twitter",
                    agent_names=self.agent_names,
                    action_logger=self.action_logger,
                    limit=3
                )
                
                if (round_num + 1) % 10 == 0 or round_num == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    progress = (round_num + 1) / total_rounds * 100
                    print(f"  [Day {simulated_day}, {simulated_hour:02d}:00] "
                          f"Round {round_num + 1}/{total_rounds} ({progress:.1f}%) "
                          f"- Synthetic pulse active ({round_action_count} actions)")
                          
                # Sleep to simulate time passing
                await asyncio.sleep(0.5)
                continue

            # Get active agents for this round
            active_agents = self._get_active_agents_for_round(
                self.env, simulated_hour, round_num
            )
            
            if not active_agents:
                continue
            
            # Construct actions
            if not demo_mode:
                actions = {
                    agent: LLMAction()
                    for _, agent in active_agents
                }
                
                # Execute actions
                await self.env.step(actions)
            
            # Print progress
            if (round_num + 1) % 10 == 0 or round_num == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                progress = (round_num + 1) / total_rounds * 100
                print(f"  [Day {simulated_day}, {simulated_hour:02d}:00] "
                      f"Round {round_num + 1}/{total_rounds} ({progress:.1f}%) "
                      f"- {len(active_agents) if not demo_mode else 'Synthetic'} agents active "
                      f"- elapsed: {elapsed:.1f}s")
        
        total_elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\nSimulation loop complete!")
        print(f"  - Total time: {total_elapsed:.1f}s")
        if not demo_mode:
            print(f"  - Database: {db_path}")
        
        # Wait for command mode
        if self.wait_for_commands:
            print("\n" + "=" * 60)
            print("Entering Wait-for-Command Mode - Environment active")
            print("Supported commands: interview, batch_interview, close_env")
            print("=" * 60)
            
            self.ipc_handler.update_status("alive")
            
            # Wait for command loop (uses global _shutdown_event)
            try:
                while not _shutdown_event.is_set():
                    should_continue = await self.ipc_handler.process_commands(demo_mode=demo_mode)
                    if not should_continue:
                        break
                    try:
                        await asyncio.wait_for(_shutdown_event.wait(), timeout=0.5)
                        break  # Signal received
                    except asyncio.TimeoutError:
                        pass
            except KeyboardInterrupt:
                print("\nReceived interrupt signal")
            except asyncio.CancelledError:
                print("\nTask cancelled")
            except Exception as e:
                print(f"\nCommand processing error: {e}")
            
            print("\nClosing environment...")
        
        # Close environment
        self.ipc_handler.update_status("stopped")
        if not demo_mode and self.env:
            await self.env.close()
        
        print("Environment closed")
        print("=" * 60)


async def main():
    parser = argparse.ArgumentParser(description='OASIS Twitter Simulation')
    parser.add_argument(
        '--config', 
        type=str, 
        required=True,
        help='Config file path (simulation_config.json)'
    )
    parser.add_argument(
        '--max-rounds',
        type=int,
        default=None,
        help='Max simulation rounds (optional, used to truncate long simulations)'
    )
    parser.add_argument(
        '--no-wait',
        action='store_true',
        default=False,
        help='Close environment immediately after simulation, do not enter wait-for-command mode'
    )
    
    args = parser.parse_args()
    
    # 在 main 函数开始时创建 shutdown 事件
    global _shutdown_event
    _shutdown_event = asyncio.Event()
    
    if not os.path.exists(args.config):
        print(f"Error: Config file does not exist: {args.config}")
        sys.exit(1)
    
    # Initialize log config (use fixed filenames, clean old logs)
    simulation_dir = os.path.dirname(args.config) or "."
    setup_oasis_logging(os.path.join(simulation_dir, "log"))
    
    runner = TwitterSimulationRunner(
        config_path=args.config,
        wait_for_commands=not args.no_wait
    )
    await runner.run(max_rounds=args.max_rounds)


def setup_signal_handlers():
    """
    Set signal handlers to ensure clean exit on SIGTERM/SIGINT
    Gives program chance to clean up resources (DB, environment, etc.)
    """
    def signal_handler(signum, frame):
        global _cleanup_done
        sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        print(f"\nReceived {sig_name} signal, exiting...")
        if not _cleanup_done:
            _cleanup_done = True
            if _shutdown_event:
                _shutdown_event.set()
        else:
            # Force exit on repeated signal
            print("Force exit...")
            sys.exit(1)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    setup_signal_handlers()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted")
    except SystemExit:
        pass
    finally:
        print("Simulation process exited")
