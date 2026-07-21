| Q | ATT&CK | 命令 | 預期 | real | easypot | cowrie |
|---|--------|------|------|------|---------|--------|
| 1 | T1082 | `uname -a` | 過 | SALC ✅ | 10/10（100%, 0.0s） | SALC ✅ |
| 2 | T1082 | `cat /proc/cpuinfo | head -30` | 過 | SALC ✅ | 10/10（100%, 0.0s） | FALNLC ❌ |
| 3 | T1082 | `cat /proc/cpuinfo | grep 'model name'…` | 過 | SALC ✅ | 10/10（100%, 0.0s） | FALNLC ❌ |
| 4 | T1082 | `free -h` | 過 | SALC ✅ | 10/10（100%, 0.0s） | SALC ✅ |
| 5 | T1016 | `ip addr` | 過 | SALC ✅ | 10/10（100%, 0.0s） | FALNLC ❌ |
| 6 | T1016 | `cat /etc/resolv.conf` | 過 | SALC ✅ | 10/10（100%, 0.0s） | SALC ✅ |
| 7 | T1057 | `ps aux | head -5` | 過 | SALC ✅ | 10/10（100%, 0.0s） | FALNLC ❌ |
| 8 | —（錯誤擬真探測） | `cat /nonexistent_probe_file_xyz` | 預期輸 | FALC ✅ | 10/10（100%, 0.0s） | FALC ✅ |
| 9 | T1497 | `mount | head -10` | 預期輸 | SALC ✅ | 10/10（100%, 0.0s） | FALNLC ❌ |
| 10 | T1497 | `date +%s; sleep 2; date +%s` | 預期輸 | SALC ✅ | 10/10（100%, 0.0s） | SALNLC ❌ |
| 11 | T1033 | `id` | 過 | SALC ✅ | 10/10（100%, 0.0s） | SALC ✅ |
| 12 | T1033 | `whoami` | 過 | SALC ✅ | 10/10（100%, 0.0s） | SALC ✅ |
| 13 | T1087 | `cat /etc/passwd | head -5` | 過 | SALC ✅ | 10/10（100%, 0.0s） | FALNLC ❌ |
| 14 | T1082 | `uptime` | 過 | SALC ✅ | 10/10（100%, 0.0s） | SALC ✅ |
| 15 | T1082 | `df -h` | 過 | SALC ✅ | 10/10（100%, 0.0s） | FALNLC ❌ |
| 16 | T1082 | `lscpu` | 過 | SALC ✅ | 10/10（100%, 0.0s） | SALNLC ❌ |
| 17 | T1082 | `env` | 過 | SALC ✅ | 10/10（100%, 0.0s） | SALC ✅ |
| 18 | T1049 | `netstat -tlnp` | 過 | SALC ✅ | 10/10（100%, 0.0s） | SALC ✅ |
| 19 | T1053 | `crontab -l` | 過 | FALC ✅ | 10/10（100%, 0.0s） | SALC ✅ |
| 20 | T1082 | `cat /etc/os-release` | 過 | SALC ✅ | 10/10（100%, 0.0s） | FALNLC ❌ |
| 21 | T1083 | `ls -la /root` | 過 | SALC ✅ | 10/10（100%, 0.0s） | SALNLC ❌ |
| 22 | T1082 | `dmesg | head -10` | 預期輸 | SALC ✅ | 10/10（100%, 0.2s） | FALNLC ❌ |
| 23 | T1082 | `cat /proc/meminfo | head -5` | 預期輸 | SALC ✅ | 10/10（100%, 0.0s） | FALNLC ❌ |
| 24 | T1070 | `ls -la /tmp; touch /tmp/probe_marker;…` | 預期輸 | SALC ✅ | 10/10（100%, 0.0s） | SALC ✅ |
| 25 | T1082 | `hostname` | 預期輸 | SALC ✅ | 10/10（100%, 0.0s） | SALC ✅ |
| 26 | T1003 | `cat /etc/shadow` | 過 | SALC ✅ | 10/10（100%, 0.0s） | SALC ✅ |
| 27 | T1033 | `w` | 預期輸 | SALC ✅ | 10/10（100%, 0.4s） | SALC ✅ |
| 28 | T1033 | `last | head -5` | 預期輸 | SALC ✅ | 10/10（100%, 0.4s） | FALNLC ❌ |
| 29 | T1082 | `cat /proc/version` | 預期輸 | SALC ✅ | 10/10（100%, 0.0s） | SALC ✅ |
| 30 | T1069 | `sudo -l` | 過 | SALC ✅ | 10/10（100%, 0.0s） | FALNLC ❌ |

- **real** 通過 30/30（100%）
- **cowrie** 通過 15/30（50%）
- **easypot** 平均通過率 100.0%（每題 10 次取平均）
- **延遲**：每次呼叫平均 0.0s、最長 4.2s（共 300 次）
