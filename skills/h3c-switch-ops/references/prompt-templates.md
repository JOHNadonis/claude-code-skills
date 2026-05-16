# Prompt Templates

## New Build

```text
帮我生成一台华三交换机配置。
版本：Comware 7
主机名：ACCESS-SW01
VLAN：10 办公网，20 语音网，99 管理网
端口：1-12 办公网 access vlan 10；13-20 语音网 access vlan 20；23-24 上联聚合
管理地址：192.168.99.2/24，网关 192.168.99.1
要求：输出目标配置、变更命令、回滚命令、验证命令
```

## Migration

```text
把这份华三旧交换机配置迁移到新设备，目标是 Comware 7。
请先解析旧配置，再输出迁移建议、目标配置、回滚和风险点。
```

## Live Collection Then Plan

```text
先采集这台华三交换机现网信息，再给我做变更方案。
主机：10.0.0.10
协议：SSH
用户名：admin
需求：新增 VLAN 20，并把 1/0/5-1/0/8 加入 access vlan 20
```

## Live Execution

```text
这台华三交换机我已经确认可以变更。
请先采集，再生成变更，再等我确认后执行。
主机：10.0.0.10
协议：SSH
用户名：admin
命令文件：/path/to/commands.txt
```

## Read-Only Validation

```text
先对这台华三老交换机做一次只读验证。
要求：不要下发任何配置，只做 SSH/Telnet 采集、解析当前配置、生成计划演练和验证报告。
主机：10.0.0.10
用户名：admin
协议：自动尝试 SSH，失败后再试 Telnet
输出目录：/tmp/h3c-real-check/sw01
```
