# AUX Climate - Home Assistant 自定义集成

通过 Broadlink（博联）红外遥控器控制 AUX（奥克斯）空调的 HA 自定义组件。无需 MQTT 中间件，直接局域网 UDP 通信。

## 工作原理

HA → 集成 → Broadlink 红外设备 → 空调

替代原来的 Docker + MQTT 方案，去掉中间环节，直接在 HA 内部完成所有通信。

## 功能

### Climate 实体（空调主控制）

| 功能 | 说明 |
|---|---|
| 开关机 | 支持（注：部分机型电源控制位偏移略有差异，需校准） |
| 温度设定 | 16°C ~ 32°C，步长 0.5°C |
| 模式切换 | 制冷 / 制热 / 除湿 / 送风 / 自动 / 关闭 |
| 风速 | Auto / Low / Medium / High / Turbo / Mute |
| 垂直扫风 | TOP / MIDDLE1~3 / BOTTOM / SWING / AUTO |

### Sensor 实体（传感器数据）

| 传感器 | 说明 | 单位 |
|---|---|---|
| 室内温度 | 空调检测的房间温度 | °C |
| 室内湿度 | 空调检测的房间湿度 | % |
| 错误代码 | 空调故障代码（0=正常） | - |

> 温度和湿度数据来自空调自身传感器，非独立温湿度计。

### Switch 实体（额外功能开关）

| 开关 | 说明 | 图标 |
|---|---|---|
| 睡眠模式 | 开启后空调自动调节运行 | `mdi:sleep` |
| 面板显示 | 控制空调面板指示灯 | `mdi:monitor-dashboard` |
| 健康模式 | 健康模式开关 | `mdi:shield-check` |
| 自清洁 | 蒸发器自清洁功能 | `mdi:water-pump` |
| 防霉 | 关机后防霉干燥功能 | `mdi:water-off` |
| 静音模式 | 静音运行 | `mdi:volume-off` |
| 强力模式 | 快速制冷/制热 | `mdi:weather-windy` |
| 调试日志 | 记录原始通信数据到文件（用于诊断） | `mdi:text-box-search-outline` |

### Select 实体（水平摆风）

| 选项 | 说明 |
|---|---|
| LEFT_FIX | 左固定 |
| LEFT_FLAP | 左摆风 |
| LEFT_RIGHT_FIX | 左右固定 |
| LEFT_RIGHT_FLAP | 左右摆风 |
| RIGHT_FIX | 右固定 |
| RIGHT_FLAP | 右摆风 |

## 安装

### 前提条件

- Home Assistant 已安装
- Broadlink（博联）红外遥控器（如 RM Mini3、RM Pro+ 等）
- 空调已能被 Broadlink 设备控制（手机 App 可正常操作）

### 安装步骤

1. 将 `aux_climate` 文件夹复制到 HA 的 `custom_components` 目录：
   ```bash
   docker cp aux_climate homeassistant:/config/custom_components/aux_climate
   docker restart homeassistant
   ```
   或手动复制到 HA 配置目录下的 `custom_components/aux_climate/`

2. 重启 Home Assistant

3. 添加集成：
   - 设置 → 设备与服务 → 右下角"添加集成"
   - 搜索 **AUX Climate**
   - 填写配置信息：
     - **名称**：自定义（如"客厅空调"）
     - **IP 地址**：空调 IP（如 `192.168.1.116`）
     - **MAC 地址**：空调 MAC，去掉冒号（如 `34ea34f76efa`）
     - **端口**：默认 `80`

## 配置示例

```
IP:     192.168.1.116
MAC:    34ea34f76efa
端口:   80
名称:   客厅空调
```

MAC 地址从路由器后台或 Broadlink App 中获取。

## 调试日志

当需要排查问题时：

1. 在 HA → 设备 → 客厅空调 → 打开 **调试日志** 开关
2. 等待 30 秒或操作空调触发数据采集
3. 关闭开关
4. 读取集成目录下的 `broadlink/ac_raw_log.txt` 文件

> 日志文件包含解密后的原始 UDP 数据包，默认关闭，不写文件。

## 常见问题

### Q: 添加集成时报"连接空调超时"
- 确认 IP 地址正确
- 确认空调和 HA 在同一局域网
- 尝试 ping 空调 IP 看是否通
- 如果网络偶尔延迟，集成会自动重试（超时前重试 10 秒）

### Q: 添加集成时报"初始化空调失败"
- 确认 MAC 地址格式正确（12位十六进制，无冒号）
- 确认 Broadlink 设备已通过手机 App 配置过
- 部分空调需要先用 Broadlink App 学习遥控器信号

### Q: 空调模式显示不正常
- 首次添加后等待 30 秒自动刷新
- 如果持续异常，检查空调网络连接

### Q: 如何获取空调 MAC 地址？
- 路由器 DHCP 客户端列表
- Broadlink App 中设备详情页
- 通过手机扫描局域网设备

### Q: 传感器显示"未知"
- 首次添加等待 30 秒自动轮询
- 如果持续"未知"，打开调试日志，分析原始数据包字节偏移

### Q: 开关面板显示/睡眠等失败
- 重启 HA 后重试
- 如果日志提示 `missing positional argument`，检查 `switch.py` 中 lambda 调用是否正确传递 `self._device`

## 文件结构

```
custom_components/aux_climate/
├── __init__.py          # 集成入口，设备注册
├── manifest.json        # 元信息
├── config_flow.py       # UI 配置流程
├── climate.py           # Climate 实体（主控制）
├── sensor.py            # Sensor 实体（温湿度、错误代码）
├── switch.py            # Switch 实体（睡眠/显示/静音/调试日志等）
├── select.py            # Select 实体（水平摆风）
└── broadlink/
    ├── ac_db.py         # Broadlink 通信协议（UDP + AES加密）
    └── ac_raw_log.txt   # 调试日志文件（默认不存在，开关打开后生成）
```

## 技术说明

- **通信协议**：UDP 局域网直连，不经过云服务
- **轮询间隔**：30 秒（自动缓存，减少网络请求）
- **加密**：AES-CBC 128bit 加密通信
- **依赖**：`pycryptodome`（AES 加密解密）
- **Python 版本**：兼容 Python 3（HA 运行环境）
- **数据包分析**：
  - `get_ac_info`（48字节）：室内温度（byte17 & 0x1F）、湿度（byte18 & 0x7F）
  - `get_ac_states`（32字节）：设定温度、运行模式、风速、扫风等

## 已知问题

- **电源控制**：部分空调机型电源控制位可能偏移，HA 关闭界面不保证物理关闭空调。通过 `ac_raw_log.txt` 对比空调真关 vs HA 关的数据差异可校准
- **修改历史**：本集成经过多次协议分析与修复，详见 `.workbuddy/memory/` 目录

## 许可

本项目基于 broadlink_ac_mqtt 开源项目改造，仅供个人学习使用。
