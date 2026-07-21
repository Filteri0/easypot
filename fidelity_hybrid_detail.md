# 擬真度細項（每題 10 次）


## Q1 uname -a
- ATT&CK：T1082 System Information Discovery
- 考點：格式擬真：核心資訊欄位順序（kernel name / hostname / release / version / machine）齊全且順序正確
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux svr04 5.10.0-19-amd64 #1 SMP Debian 5.10.0-19-amd64 x86_64 GNU/Linux

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux svr04 5.10.0-19-amd64 #1 SMP Debian 5.10.0-19-amd64 x86_64 GNU/Linux

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux svr04 5.10.0-19-amd64 #1 SMP Debian 5.10.0-19-amd64 x86_64 GNU/Linux

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux svr04 5.10.0-19-amd64 #1 SMP Debian 5.10.0-19-amd64 x86_64 GNU/Linux

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux svr04 5.10.0-19-amd64 #1 SMP Debian 5.10.0-19-amd64 x86_64 GNU/Linux

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux svr04 5.10.0-19-amd64 #1 SMP Debian 5.10.0-19-amd64 x86_64 GNU/Linux

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux svr04 5.10.0-19-amd64 #1 SMP Debian 5.10.0-19-amd64 x86_64 GNU/Linux

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux svr04 5.10.0-19-amd64 #1 SMP Debian 5.10.0-19-amd64 x86_64 GNU/Linux

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux svr04 5.10.0-19-amd64 #1 SMP Debian 5.10.0-19-amd64 x86_64 GNU/Linux

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux svr04 5.10.0-19-amd64 #1 SMP Debian 5.10.0-19-amd64 x86_64 GNU/Linux

```


## Q2 cat /proc/cpuinfo | head -30
- ATT&CK：T1082 System Information Discovery
- 考點：關鍵欄位存在性：processor / vendor_id / model name / cpu MHz / flags 等真機必有欄位
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 79
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0xb000038
cpu MHz		: 2400.000
cache size	: 35840 KB
physical id	: 0
siblings	: 2
core id		: 0
cpu cores	: 2
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon rep_good nopl xtopology cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch invpcid_single pti fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm rdseed adx smap xsaveopt arat
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data retbleed
bogomips	: 4800.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 46 bits physical, 48 bits virtual
power management:

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 79
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0xb000038
cpu MHz		: 2400.000
cache size	: 35840 KB
physical id	: 0
siblings	: 2
core id		: 0
cpu cores	: 2
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon rep_good nopl xtopology cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch invpcid_single pti fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm rdseed adx smap xsaveopt arat
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data retbleed
bogomips	: 4800.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 46 bits physical, 48 bits virtual
power management:

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 79
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0xb000038
cpu MHz		: 2400.000
cache size	: 35840 KB
physical id	: 0
siblings	: 2
core id		: 0
cpu cores	: 2
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon rep_good nopl xtopology cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch invpcid_single pti fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm rdseed adx smap xsaveopt arat
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data retbleed
bogomips	: 4800.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 46 bits physical, 48 bits virtual
power management:

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 79
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0xb000038
cpu MHz		: 2400.000
cache size	: 35840 KB
physical id	: 0
siblings	: 2
core id		: 0
cpu cores	: 2
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon rep_good nopl xtopology cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch invpcid_single pti fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm rdseed adx smap xsaveopt arat
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data retbleed
bogomips	: 4800.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 46 bits physical, 48 bits virtual
power management:

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 79
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0xb000038
cpu MHz		: 2400.000
cache size	: 35840 KB
physical id	: 0
siblings	: 2
core id		: 0
cpu cores	: 2
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon rep_good nopl xtopology cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch invpcid_single pti fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm rdseed adx smap xsaveopt arat
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data retbleed
bogomips	: 4800.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 46 bits physical, 48 bits virtual
power management:

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 79
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0xb000038
cpu MHz		: 2400.000
cache size	: 35840 KB
physical id	: 0
siblings	: 2
core id		: 0
cpu cores	: 2
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon rep_good nopl xtopology cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch invpcid_single pti fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm rdseed adx smap xsaveopt arat
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data retbleed
bogomips	: 4800.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 46 bits physical, 48 bits virtual
power management:

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 79
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0xb000038
cpu MHz		: 2400.000
cache size	: 35840 KB
physical id	: 0
siblings	: 2
core id		: 0
cpu cores	: 2
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon rep_good nopl xtopology cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch invpcid_single pti fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm rdseed adx smap xsaveopt arat
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data retbleed
bogomips	: 4800.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 46 bits physical, 48 bits virtual
power management:

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 79
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0xb000038
cpu MHz		: 2400.000
cache size	: 35840 KB
physical id	: 0
siblings	: 2
core id		: 0
cpu cores	: 2
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon rep_good nopl xtopology cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch invpcid_single pti fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm rdseed adx smap xsaveopt arat
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data retbleed
bogomips	: 4800.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 46 bits physical, 48 bits virtual
power management:

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 79
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0xb000038
cpu MHz		: 2400.000
cache size	: 35840 KB
physical id	: 0
siblings	: 2
core id		: 0
cpu cores	: 2
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon rep_good nopl xtopology cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch invpcid_single pti fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm rdseed adx smap xsaveopt arat
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data retbleed
bogomips	: 4800.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 46 bits physical, 48 bits virtual
power management:

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 79
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0xb000038
cpu MHz		: 2400.000
cache size	: 35840 KB
physical id	: 0
siblings	: 2
core id		: 0
cpu cores	: 2
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon rep_good nopl xtopology cpuid tsc_known_freq pni pclmulqdq ssse3 fma cx16 pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand hypervisor lahf_lm abm 3dnowprefetch invpcid_single pti fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm rdseed adx smap xsaveopt arat
bugs		: cpu_meltdown spectre_v1 spectre_v2 spec_store_bypass l1tf mds swapgs itlb_multihit mmio_stale_data retbleed
bogomips	: 4800.00
clflush size	: 64
cache_alignment	: 64
address sizes	: 46 bits physical, 48 bits virtual
power management:

processor	: 1
vendor_id	: GenuineIntel
cpu family	: 6

```


## Q3 cat /proc/cpuinfo | grep 'model name' | head -1 | awk '{print $4}'
- ATT&CK：T1082 System Information Discovery
- 考點：跨工具管線一致性：cat→grep→awk 串起來，最終欄位提取結果須與 Q2 的 model name 欄位自洽（考狀態/邏輯一致，非各自亂生）
- 通過：10/10

### 第 1 次 ✅ SALC
判定：有非空輸出

```
Intel(R)

```

### 第 2 次 ✅ SALC
判定：有非空輸出

```
Intel(R)

```

### 第 3 次 ✅ SALC
判定：有非空輸出

```
Intel(R)

```

### 第 4 次 ✅ SALC
判定：有非空輸出

```
Intel(R)

```

### 第 5 次 ✅ SALC
判定：有非空輸出

```
Intel(R)

```

### 第 6 次 ✅ SALC
判定：有非空輸出

```
Intel(R)

```

### 第 7 次 ✅ SALC
判定：有非空輸出

```
Intel(R)

```

### 第 8 次 ✅ SALC
判定：有非空輸出

```
Intel(R)

```

### 第 9 次 ✅ SALC
判定：有非空輸出

```
Intel(R)

```

### 第 10 次 ✅ SALC
判定：有非空輸出

```
Intel(R)

```


## Q4 free -h
- ATT&CK：T1082 System Information Discovery
- 考點：表頭與欄位格式：total/used/free/shared/buff/cache/available 欄位齊全，Mem: 與 Swap: 兩列，帶人類可讀單位
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
                     total       used       free     shared buff/cache  available
Mem:                 8.0Gi      2.8Gi      5.2Gi      163Mi      1.6Gi      6.8Gi
Swap:                8.0Gi        0Mi      8.0Gi

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
                     total       used       free     shared buff/cache  available
Mem:                 8.0Gi      2.8Gi      5.2Gi      163Mi      1.6Gi      6.8Gi
Swap:                8.0Gi        0Mi      8.0Gi

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
                     total       used       free     shared buff/cache  available
Mem:                 8.0Gi      2.8Gi      5.2Gi      163Mi      1.6Gi      6.8Gi
Swap:                8.0Gi        0Mi      8.0Gi

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
                     total       used       free     shared buff/cache  available
Mem:                 8.0Gi      2.8Gi      5.2Gi      163Mi      1.6Gi      6.8Gi
Swap:                8.0Gi        0Mi      8.0Gi

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
                     total       used       free     shared buff/cache  available
Mem:                 8.0Gi      2.8Gi      5.2Gi      163Mi      1.6Gi      6.8Gi
Swap:                8.0Gi        0Mi      8.0Gi

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
                     total       used       free     shared buff/cache  available
Mem:                 8.0Gi      2.8Gi      5.2Gi      163Mi      1.6Gi      6.8Gi
Swap:                8.0Gi        0Mi      8.0Gi

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
                     total       used       free     shared buff/cache  available
Mem:                 8.0Gi      2.8Gi      5.2Gi      163Mi      1.6Gi      6.8Gi
Swap:                8.0Gi        0Mi      8.0Gi

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
                     total       used       free     shared buff/cache  available
Mem:                 8.0Gi      2.8Gi      5.2Gi      163Mi      1.6Gi      6.8Gi
Swap:                8.0Gi        0Mi      8.0Gi

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
                     total       used       free     shared buff/cache  available
Mem:                 8.0Gi      2.8Gi      5.2Gi      163Mi      1.6Gi      6.8Gi
Swap:                8.0Gi        0Mi      8.0Gi

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
                     total       used       free     shared buff/cache  available
Mem:                 8.0Gi      2.8Gi      5.2Gi      163Mi      1.6Gi      6.8Gi
Swap:                8.0Gi        0Mi      8.0Gi

```


## Q5 ip addr
- ATT&CK：T1016 System Network Configuration Discovery
- 考點：介面/位址格式：至少 lo + 一個實體介面，含 inet 行、MAC（link/ether）、編號前綴（1: 2:）
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:1a:a0:3f:7c:12 brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.24/24 brd 10.0.0.255 scope global eth0

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:1a:a0:3f:7c:12 brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.24/24 brd 10.0.0.255 scope global eth0

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:1a:a0:3f:7c:12 brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.24/24 brd 10.0.0.255 scope global eth0

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:1a:a0:3f:7c:12 brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.24/24 brd 10.0.0.255 scope global eth0

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:1a:a0:3f:7c:12 brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.24/24 brd 10.0.0.255 scope global eth0

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:1a:a0:3f:7c:12 brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.24/24 brd 10.0.0.255 scope global eth0

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:1a:a0:3f:7c:12 brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.24/24 brd 10.0.0.255 scope global eth0

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:1a:a0:3f:7c:12 brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.24/24 brd 10.0.0.255 scope global eth0

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:1a:a0:3f:7c:12 brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.24/24 brd 10.0.0.255 scope global eth0

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:1a:a0:3f:7c:12 brd ff:ff:ff:ff:ff:ff
    inet 10.0.0.24/24 brd 10.0.0.255 scope global eth0

```


## Q6 cat /etc/resolv.conf
- ATT&CK：T1016 System Network Configuration Discovery
- 考點：檔案內容擬真：nameserver 行格式正確
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
# This file is managed by man:systemd-resolved(8). Do not edit.
nameserver 8.8.8.8
nameserver 1.1.1.1
search localdomain

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
# This file is managed by man:systemd-resolved(8). Do not edit.
nameserver 8.8.8.8
nameserver 1.1.1.1
search localdomain

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
# This file is managed by man:systemd-resolved(8). Do not edit.
nameserver 8.8.8.8
nameserver 1.1.1.1
search localdomain

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
# This file is managed by man:systemd-resolved(8). Do not edit.
nameserver 8.8.8.8
nameserver 1.1.1.1
search localdomain

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
# This file is managed by man:systemd-resolved(8). Do not edit.
nameserver 8.8.8.8
nameserver 1.1.1.1
search localdomain

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
# This file is managed by man:systemd-resolved(8). Do not edit.
nameserver 8.8.8.8
nameserver 1.1.1.1
search localdomain

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
# This file is managed by man:systemd-resolved(8). Do not edit.
nameserver 8.8.8.8
nameserver 1.1.1.1
search localdomain

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
# This file is managed by man:systemd-resolved(8). Do not edit.
nameserver 8.8.8.8
nameserver 1.1.1.1
search localdomain

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
# This file is managed by man:systemd-resolved(8). Do not edit.
nameserver 8.8.8.8
nameserver 1.1.1.1
search localdomain

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
# This file is managed by man:systemd-resolved(8). Do not edit.
nameserver 8.8.8.8
nameserver 1.1.1.1
search localdomain

```


## Q7 ps aux | head -5
- ATT&CK：T1057 Process Discovery
- 考點：表頭欄位順序：USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND；且第一列通常是 root 的 PID 1
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER        PID  %CPU  %MEM     VSZ    RSS TTY      STAT START   TIME COMMAND
root          1   0.0   0.1  167404  11876 ?        Ss   05:22   0:04 /sbin/init
root          2   0.0   0.1       0      0 ?        S    05:22   0:00 [kthreadd]
root        411   0.0   0.1   46752   8564 ?        Ss   05:22   0:12 /lib/systemd/systemd-journald
root        439   0.0   0.1   22932   5412 ?        Ss   05:22   0:01 /lib/systemd/systemd-udevd

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER        PID  %CPU  %MEM     VSZ    RSS TTY      STAT START   TIME COMMAND
root          1   0.0   0.1  167404  11876 ?        Ss   05:22   0:04 /sbin/init
root          2   0.0   0.1       0      0 ?        S    05:22   0:00 [kthreadd]
root        411   0.0   0.1   46752   8564 ?        Ss   05:22   0:12 /lib/systemd/systemd-journald
root        439   0.0   0.1   22932   5412 ?        Ss   05:22   0:01 /lib/systemd/systemd-udevd

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER        PID  %CPU  %MEM     VSZ    RSS TTY      STAT START   TIME COMMAND
root          1   0.0   0.1  167404  11876 ?        Ss   05:22   0:04 /sbin/init
root          2   0.0   0.1       0      0 ?        S    05:22   0:00 [kthreadd]
root        411   0.0   0.1   46752   8564 ?        Ss   05:22   0:12 /lib/systemd/systemd-journald
root        439   0.0   0.1   22932   5412 ?        Ss   05:22   0:01 /lib/systemd/systemd-udevd

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER        PID  %CPU  %MEM     VSZ    RSS TTY      STAT START   TIME COMMAND
root          1   0.0   0.1  167404  11876 ?        Ss   05:22   0:04 /sbin/init
root          2   0.0   0.1       0      0 ?        S    05:22   0:00 [kthreadd]
root        411   0.0   0.1   46752   8564 ?        Ss   05:22   0:12 /lib/systemd/systemd-journald
root        439   0.0   0.1   22932   5412 ?        Ss   05:22   0:01 /lib/systemd/systemd-udevd

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER        PID  %CPU  %MEM     VSZ    RSS TTY      STAT START   TIME COMMAND
root          1   0.0   0.1  167404  11876 ?        Ss   05:22   0:04 /sbin/init
root          2   0.0   0.1       0      0 ?        S    05:22   0:00 [kthreadd]
root        411   0.0   0.1   46752   8564 ?        Ss   05:22   0:12 /lib/systemd/systemd-journald
root        439   0.0   0.1   22932   5412 ?        Ss   05:22   0:01 /lib/systemd/systemd-udevd

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER        PID  %CPU  %MEM     VSZ    RSS TTY      STAT START   TIME COMMAND
root          1   0.0   0.1  167404  11876 ?        Ss   05:22   0:04 /sbin/init
root          2   0.0   0.1       0      0 ?        S    05:22   0:00 [kthreadd]
root        411   0.0   0.1   46752   8564 ?        Ss   05:22   0:12 /lib/systemd/systemd-journald
root        439   0.0   0.1   22932   5412 ?        Ss   05:22   0:01 /lib/systemd/systemd-udevd

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER        PID  %CPU  %MEM     VSZ    RSS TTY      STAT START   TIME COMMAND
root          1   0.0   0.1  167404  11876 ?        Ss   05:22   0:04 /sbin/init
root          2   0.0   0.1       0      0 ?        S    05:22   0:00 [kthreadd]
root        411   0.0   0.1   46752   8564 ?        Ss   05:22   0:12 /lib/systemd/systemd-journald
root        439   0.0   0.1   22932   5412 ?        Ss   05:22   0:01 /lib/systemd/systemd-udevd

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER        PID  %CPU  %MEM     VSZ    RSS TTY      STAT START   TIME COMMAND
root          1   0.0   0.1  167404  11876 ?        Ss   05:22   0:04 /sbin/init
root          2   0.0   0.1       0      0 ?        S    05:22   0:00 [kthreadd]
root        411   0.0   0.1   46752   8564 ?        Ss   05:22   0:12 /lib/systemd/systemd-journald
root        439   0.0   0.1   22932   5412 ?        Ss   05:22   0:01 /lib/systemd/systemd-udevd

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER        PID  %CPU  %MEM     VSZ    RSS TTY      STAT START   TIME COMMAND
root          1   0.0   0.1  167404  11876 ?        Ss   05:22   0:04 /sbin/init
root          2   0.0   0.1       0      0 ?        S    05:22   0:00 [kthreadd]
root        411   0.0   0.1   46752   8564 ?        Ss   05:22   0:12 /lib/systemd/systemd-journald
root        439   0.0   0.1   22932   5412 ?        Ss   05:22   0:01 /lib/systemd/systemd-udevd

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER        PID  %CPU  %MEM     VSZ    RSS TTY      STAT START   TIME COMMAND
root          1   0.0   0.1  167404  11876 ?        Ss   05:22   0:04 /sbin/init
root          2   0.0   0.1       0      0 ?        S    05:22   0:00 [kthreadd]
root        411   0.0   0.1   46752   8564 ?        Ss   05:22   0:12 /lib/systemd/systemd-journald
root        439   0.0   0.1   22932   5412 ?        Ss   05:22   0:01 /lib/systemd/systemd-udevd

```


## Q8 cat /nonexistent_probe_file_xyz
- ATT&CK：—（錯誤擬真探測）
- 考點：錯誤擬真：真機應回精確錯誤 'cat: <path>: No such file or directory' 且 exit≠0；easypot 的 LLM 可能過度熱心假裝成功或亂編內容 → 露餡
- 通過：10/10

### 第 1 次 ✅ FALC
判定：給出真機式的 'No such file or directory' 錯誤

```
cat: /nonexistent_probe_file_xyz: No such file or directory

```

### 第 2 次 ✅ FALC
判定：給出真機式的 'No such file or directory' 錯誤

```
cat: /nonexistent_probe_file_xyz: No such file or directory

```

### 第 3 次 ✅ FALC
判定：給出真機式的 'No such file or directory' 錯誤

```
cat: /nonexistent_probe_file_xyz: No such file or directory

```

### 第 4 次 ✅ FALC
判定：給出真機式的 'No such file or directory' 錯誤

```
cat: /nonexistent_probe_file_xyz: No such file or directory

```

### 第 5 次 ✅ FALC
判定：給出真機式的 'No such file or directory' 錯誤

```
cat: /nonexistent_probe_file_xyz: No such file or directory

```

### 第 6 次 ✅ FALC
判定：給出真機式的 'No such file or directory' 錯誤

```
cat: /nonexistent_probe_file_xyz: No such file or directory

```

### 第 7 次 ✅ FALC
判定：給出真機式的 'No such file or directory' 錯誤

```
cat: /nonexistent_probe_file_xyz: No such file or directory

```

### 第 8 次 ✅ FALC
判定：給出真機式的 'No such file or directory' 錯誤

```
cat: /nonexistent_probe_file_xyz: No such file or directory

```

### 第 9 次 ✅ FALC
判定：給出真機式的 'No such file or directory' 錯誤

```
cat: /nonexistent_probe_file_xyz: No such file or directory

```

### 第 10 次 ✅ FALC
判定：給出真機式的 'No such file or directory' 錯誤

```
cat: /nonexistent_probe_file_xyz: No such file or directory

```


## Q9 mount | head -10
- ATT&CK：T1497 Virtualization/Sandbox Evasion
- 考點：掛載表擬真：真機應見 proc/sysfs/devpts/tmpfs 等偽檔案系統 + 根 / 掛載；蜜罐常給不出真實掛載結構 → 露餡
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=4074512k,nr_inodes=1018628,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
tmpfs on /run type tmpfs (rw,nosuid,nodev,noexec,relatime,size=819200k,mode=755)
/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro)
tmpfs on /dev/shm type tmpfs (rw,nosuid,nodev)
tmpfs on /run/lock type tmpfs (rw,nosuid,nodev,noexec,relatime,size=5120k)

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=4074512k,nr_inodes=1018628,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
tmpfs on /run type tmpfs (rw,nosuid,nodev,noexec,relatime,size=819200k,mode=755)
/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro)
tmpfs on /dev/shm type tmpfs (rw,nosuid,nodev)
tmpfs on /run/lock type tmpfs (rw,nosuid,nodev,noexec,relatime,size=5120k)

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=4074512k,nr_inodes=1018628,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
tmpfs on /run type tmpfs (rw,nosuid,nodev,noexec,relatime,size=819200k,mode=755)
/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro)
tmpfs on /dev/shm type tmpfs (rw,nosuid,nodev)
tmpfs on /run/lock type tmpfs (rw,nosuid,nodev,noexec,relatime,size=5120k)

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=4074512k,nr_inodes=1018628,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
tmpfs on /run type tmpfs (rw,nosuid,nodev,noexec,relatime,size=819200k,mode=755)
/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro)
tmpfs on /dev/shm type tmpfs (rw,nosuid,nodev)
tmpfs on /run/lock type tmpfs (rw,nosuid,nodev,noexec,relatime,size=5120k)

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=4074512k,nr_inodes=1018628,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
tmpfs on /run type tmpfs (rw,nosuid,nodev,noexec,relatime,size=819200k,mode=755)
/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro)
tmpfs on /dev/shm type tmpfs (rw,nosuid,nodev)
tmpfs on /run/lock type tmpfs (rw,nosuid,nodev,noexec,relatime,size=5120k)

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=4074512k,nr_inodes=1018628,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
tmpfs on /run type tmpfs (rw,nosuid,nodev,noexec,relatime,size=819200k,mode=755)
/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro)
tmpfs on /dev/shm type tmpfs (rw,nosuid,nodev)
tmpfs on /run/lock type tmpfs (rw,nosuid,nodev,noexec,relatime,size=5120k)

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=4074512k,nr_inodes=1018628,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
tmpfs on /run type tmpfs (rw,nosuid,nodev,noexec,relatime,size=819200k,mode=755)
/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro)
tmpfs on /dev/shm type tmpfs (rw,nosuid,nodev)
tmpfs on /run/lock type tmpfs (rw,nosuid,nodev,noexec,relatime,size=5120k)

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=4074512k,nr_inodes=1018628,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
tmpfs on /run type tmpfs (rw,nosuid,nodev,noexec,relatime,size=819200k,mode=755)
/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro)
tmpfs on /dev/shm type tmpfs (rw,nosuid,nodev)
tmpfs on /run/lock type tmpfs (rw,nosuid,nodev,noexec,relatime,size=5120k)

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=4074512k,nr_inodes=1018628,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
tmpfs on /run type tmpfs (rw,nosuid,nodev,noexec,relatime,size=819200k,mode=755)
/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro)
tmpfs on /dev/shm type tmpfs (rw,nosuid,nodev)
tmpfs on /run/lock type tmpfs (rw,nosuid,nodev,noexec,relatime,size=5120k)

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=4074512k,nr_inodes=1018628,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
tmpfs on /run type tmpfs (rw,nosuid,nodev,noexec,relatime,size=819200k,mode=755)
/dev/sda1 on / type ext4 (rw,relatime,errors=remount-ro)
tmpfs on /dev/shm type tmpfs (rw,nosuid,nodev)
tmpfs on /run/lock type tmpfs (rw,nosuid,nodev,noexec,relatime,size=5120k)

```


## Q10 date +%s; sleep 2; date +%s
- ATT&CK：T1497 Virtualization/Sandbox Evasion
- 考點：跨命令狀態一致性（§6 process model）：第二個時間戳應比第一個大約 2（±1）。考蜜罐能否維持時間流動一致，而非兩次憑空生成無關數字。這是 easypot 單命令無狀態設計最可能輸的題。
- 通過：10/10

### 第 1 次 ✅ SALC
判定：兩個時間戳差 2s，跨命令時間一致

```
1784586792
1784586794

```

### 第 2 次 ✅ SALC
判定：兩個時間戳差 2s，跨命令時間一致

```
1784586792
1784586794

```

### 第 3 次 ✅ SALC
判定：兩個時間戳差 2s，跨命令時間一致

```
1784586792
1784586794

```

### 第 4 次 ✅ SALC
判定：兩個時間戳差 2s，跨命令時間一致

```
1784586792
1784586794

```

### 第 5 次 ✅ SALC
判定：兩個時間戳差 2s，跨命令時間一致

```
1784586792
1784586794

```

### 第 6 次 ✅ SALC
判定：兩個時間戳差 2s，跨命令時間一致

```
1784586792
1784586794

```

### 第 7 次 ✅ SALC
判定：兩個時間戳差 2s，跨命令時間一致

```
1784586792
1784586794

```

### 第 8 次 ✅ SALC
判定：兩個時間戳差 2s，跨命令時間一致

```
1784586792
1784586794

```

### 第 9 次 ✅ SALC
判定：兩個時間戳差 2s，跨命令時間一致

```
1784586792
1784586794

```

### 第 10 次 ✅ SALC
判定：兩個時間戳差 2s，跨命令時間一致

```
1784586792
1784586794

```


## Q11 id
- ATT&CK：T1033 System Owner/User Discovery
- 考點：格式：uid=0(root) gid=0(root) groups=... 樣式
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
uid=0(root) gid=0(root) groups=0(root)

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
uid=0(root) gid=0(root) groups=0(root)

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
uid=0(root) gid=0(root) groups=0(root)

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
uid=0(root) gid=0(root) groups=0(root)

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
uid=0(root) gid=0(root) groups=0(root)

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
uid=0(root) gid=0(root) groups=0(root)

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
uid=0(root) gid=0(root) groups=0(root)

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
uid=0(root) gid=0(root) groups=0(root)

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
uid=0(root) gid=0(root) groups=0(root)

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
uid=0(root) gid=0(root) groups=0(root)

```


## Q12 whoami
- ATT&CK：T1033 System Owner/User Discovery
- 考點：單行回傳當前使用者名（root）
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root

```


## Q13 cat /etc/passwd | head -5
- ATT&CK：T1087 Account Discovery
- 考點：格式：user:x:uid:gid:comment:home:shell 七欄冒號分隔；第一列必為 root:x:0:0
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync

```


## Q14 uptime
- ATT&CK：T1082 System Information Discovery
- 考點：格式：當前時間 + up 時長 + users + load average；up 時長須與模擬時鐘一致（時間注入修復後應合理）
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 06:33:12 up 7 days,  3:14,  1 user,  load average: 0.08, 0.03, 0.01

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 06:33:12 up 7 days,  3:14,  1 user,  load average: 0.08, 0.03, 0.01

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 06:33:12 up 7 days,  3:14,  1 user,  load average: 0.08, 0.03, 0.01

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 06:33:12 up 7 days,  3:14,  1 user,  load average: 0.08, 0.03, 0.01

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 06:33:12 up 7 days,  3:14,  1 user,  load average: 0.08, 0.03, 0.01

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 06:33:12 up 7 days,  3:14,  1 user,  load average: 0.08, 0.03, 0.01

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 06:33:12 up 7 days,  3:14,  1 user,  load average: 0.08, 0.03, 0.01

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 06:33:12 up 7 days,  3:14,  1 user,  load average: 0.08, 0.03, 0.01

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 06:33:12 up 7 days,  3:14,  1 user,  load average: 0.08, 0.03, 0.01

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 06:33:12 up 7 days,  3:14,  1 user,  load average: 0.08, 0.03, 0.01

```


## Q15 df -h
- ATT&CK：T1082 System Information Discovery
- 考點：表頭 Filesystem Size Used Avail Use% Mounted；必有根 / 掛載列
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem         Size   Used  Avail Use% Mounted on
/dev/sda1         39.2G   8.5G  30.8G  22% /
tmpfs              3.9G     0B   3.9G   0% /dev/shm
tmpfs            800.0M   1.0M 799.0M   0% /run
tmpfs              5.0M     0B   5.0M   0% /run/lock

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem         Size   Used  Avail Use% Mounted on
/dev/sda1         39.2G   8.5G  30.8G  22% /
tmpfs              3.9G     0B   3.9G   0% /dev/shm
tmpfs            800.0M   1.0M 799.0M   0% /run
tmpfs              5.0M     0B   5.0M   0% /run/lock

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem         Size   Used  Avail Use% Mounted on
/dev/sda1         39.2G   8.5G  30.8G  22% /
tmpfs              3.9G     0B   3.9G   0% /dev/shm
tmpfs            800.0M   1.0M 799.0M   0% /run
tmpfs              5.0M     0B   5.0M   0% /run/lock

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem         Size   Used  Avail Use% Mounted on
/dev/sda1         39.2G   8.5G  30.8G  22% /
tmpfs              3.9G     0B   3.9G   0% /dev/shm
tmpfs            800.0M   1.0M 799.0M   0% /run
tmpfs              5.0M     0B   5.0M   0% /run/lock

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem         Size   Used  Avail Use% Mounted on
/dev/sda1         39.2G   8.5G  30.8G  22% /
tmpfs              3.9G     0B   3.9G   0% /dev/shm
tmpfs            800.0M   1.0M 799.0M   0% /run
tmpfs              5.0M     0B   5.0M   0% /run/lock

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem         Size   Used  Avail Use% Mounted on
/dev/sda1         39.2G   8.5G  30.8G  22% /
tmpfs              3.9G     0B   3.9G   0% /dev/shm
tmpfs            800.0M   1.0M 799.0M   0% /run
tmpfs              5.0M     0B   5.0M   0% /run/lock

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem         Size   Used  Avail Use% Mounted on
/dev/sda1         39.2G   8.5G  30.8G  22% /
tmpfs              3.9G     0B   3.9G   0% /dev/shm
tmpfs            800.0M   1.0M 799.0M   0% /run
tmpfs              5.0M     0B   5.0M   0% /run/lock

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem         Size   Used  Avail Use% Mounted on
/dev/sda1         39.2G   8.5G  30.8G  22% /
tmpfs              3.9G     0B   3.9G   0% /dev/shm
tmpfs            800.0M   1.0M 799.0M   0% /run
tmpfs              5.0M     0B   5.0M   0% /run/lock

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem         Size   Used  Avail Use% Mounted on
/dev/sda1         39.2G   8.5G  30.8G  22% /
tmpfs              3.9G     0B   3.9G   0% /dev/shm
tmpfs            800.0M   1.0M 799.0M   0% /run
tmpfs              5.0M     0B   5.0M   0% /run/lock

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem         Size   Used  Avail Use% Mounted on
/dev/sda1         39.2G   8.5G  30.8G  22% /
tmpfs              3.9G     0B   3.9G   0% /dev/shm
tmpfs            800.0M   1.0M 799.0M   0% /run
tmpfs              5.0M     0B   5.0M   0% /run/lock

```


## Q16 lscpu
- ATT&CK：T1082 System Information Discovery
- 考點：Architecture / CPU(s) / Model name / 欄位齊全
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Architecture:         x86_64
CPU op-mode(s):       32-bit, 64-bit
Byte Order:           Little Endian
CPU(s):               4
On-line CPU(s) list:  0-3
Thread(s) per core:   1
Core(s) per socket:   4
Socket(s):            1
Vendor ID:            GenuineIntel
Model name:           Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
CPU MHz:              2400.000
Hypervisor vendor:    KVM
Virtualization type:  full

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Architecture:         x86_64
CPU op-mode(s):       32-bit, 64-bit
Byte Order:           Little Endian
CPU(s):               4
On-line CPU(s) list:  0-3
Thread(s) per core:   1
Core(s) per socket:   4
Socket(s):            1
Vendor ID:            GenuineIntel
Model name:           Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
CPU MHz:              2400.000
Hypervisor vendor:    KVM
Virtualization type:  full

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Architecture:         x86_64
CPU op-mode(s):       32-bit, 64-bit
Byte Order:           Little Endian
CPU(s):               4
On-line CPU(s) list:  0-3
Thread(s) per core:   1
Core(s) per socket:   4
Socket(s):            1
Vendor ID:            GenuineIntel
Model name:           Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
CPU MHz:              2400.000
Hypervisor vendor:    KVM
Virtualization type:  full

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Architecture:         x86_64
CPU op-mode(s):       32-bit, 64-bit
Byte Order:           Little Endian
CPU(s):               4
On-line CPU(s) list:  0-3
Thread(s) per core:   1
Core(s) per socket:   4
Socket(s):            1
Vendor ID:            GenuineIntel
Model name:           Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
CPU MHz:              2400.000
Hypervisor vendor:    KVM
Virtualization type:  full

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Architecture:         x86_64
CPU op-mode(s):       32-bit, 64-bit
Byte Order:           Little Endian
CPU(s):               4
On-line CPU(s) list:  0-3
Thread(s) per core:   1
Core(s) per socket:   4
Socket(s):            1
Vendor ID:            GenuineIntel
Model name:           Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
CPU MHz:              2400.000
Hypervisor vendor:    KVM
Virtualization type:  full

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Architecture:         x86_64
CPU op-mode(s):       32-bit, 64-bit
Byte Order:           Little Endian
CPU(s):               4
On-line CPU(s) list:  0-3
Thread(s) per core:   1
Core(s) per socket:   4
Socket(s):            1
Vendor ID:            GenuineIntel
Model name:           Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
CPU MHz:              2400.000
Hypervisor vendor:    KVM
Virtualization type:  full

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Architecture:         x86_64
CPU op-mode(s):       32-bit, 64-bit
Byte Order:           Little Endian
CPU(s):               4
On-line CPU(s) list:  0-3
Thread(s) per core:   1
Core(s) per socket:   4
Socket(s):            1
Vendor ID:            GenuineIntel
Model name:           Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
CPU MHz:              2400.000
Hypervisor vendor:    KVM
Virtualization type:  full

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Architecture:         x86_64
CPU op-mode(s):       32-bit, 64-bit
Byte Order:           Little Endian
CPU(s):               4
On-line CPU(s) list:  0-3
Thread(s) per core:   1
Core(s) per socket:   4
Socket(s):            1
Vendor ID:            GenuineIntel
Model name:           Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
CPU MHz:              2400.000
Hypervisor vendor:    KVM
Virtualization type:  full

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Architecture:         x86_64
CPU op-mode(s):       32-bit, 64-bit
Byte Order:           Little Endian
CPU(s):               4
On-line CPU(s) list:  0-3
Thread(s) per core:   1
Core(s) per socket:   4
Socket(s):            1
Vendor ID:            GenuineIntel
Model name:           Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
CPU MHz:              2400.000
Hypervisor vendor:    KVM
Virtualization type:  full

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Architecture:         x86_64
CPU op-mode(s):       32-bit, 64-bit
Byte Order:           Little Endian
CPU(s):               4
On-line CPU(s) list:  0-3
Thread(s) per core:   1
Core(s) per socket:   4
Socket(s):            1
Vendor ID:            GenuineIntel
Model name:           Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
CPU MHz:              2400.000
Hypervisor vendor:    KVM
Virtualization type:  full

```


## Q17 env
- ATT&CK：T1082 System Information Discovery
- 考點：環境變數 KEY=VALUE 逐行；必有 PATH、HOME
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOME=/root
USER=root
PATH=/usr/bin:/bin

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOME=/root
USER=root
PATH=/usr/bin:/bin

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOME=/root
USER=root
PATH=/usr/bin:/bin

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOME=/root
USER=root
PATH=/usr/bin:/bin

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOME=/root
USER=root
PATH=/usr/bin:/bin

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOME=/root
USER=root
PATH=/usr/bin:/bin

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOME=/root
USER=root
PATH=/usr/bin:/bin

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOME=/root
USER=root
PATH=/usr/bin:/bin

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOME=/root
USER=root
PATH=/usr/bin:/bin

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOME=/root
USER=root
PATH=/usr/bin:/bin

```


## Q18 netstat -tlnp
- ATT&CK：T1049 System Network Connections Discovery
- 考點：表頭 Proto Recv-Q Send-Q Local Address；監聽埠格式
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (servers and established)
Proto  Recv-Q Send-Q Local Address         Foreign Address       State
tcp         0      0 0.0.0.0:22            0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:5432          0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:6379          0.0.0.0:*             LISTEN

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (servers and established)
Proto  Recv-Q Send-Q Local Address         Foreign Address       State
tcp         0      0 0.0.0.0:22            0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:5432          0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:6379          0.0.0.0:*             LISTEN

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (servers and established)
Proto  Recv-Q Send-Q Local Address         Foreign Address       State
tcp         0      0 0.0.0.0:22            0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:5432          0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:6379          0.0.0.0:*             LISTEN

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (servers and established)
Proto  Recv-Q Send-Q Local Address         Foreign Address       State
tcp         0      0 0.0.0.0:22            0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:5432          0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:6379          0.0.0.0:*             LISTEN

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (servers and established)
Proto  Recv-Q Send-Q Local Address         Foreign Address       State
tcp         0      0 0.0.0.0:22            0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:5432          0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:6379          0.0.0.0:*             LISTEN

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (servers and established)
Proto  Recv-Q Send-Q Local Address         Foreign Address       State
tcp         0      0 0.0.0.0:22            0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:5432          0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:6379          0.0.0.0:*             LISTEN

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (servers and established)
Proto  Recv-Q Send-Q Local Address         Foreign Address       State
tcp         0      0 0.0.0.0:22            0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:5432          0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:6379          0.0.0.0:*             LISTEN

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (servers and established)
Proto  Recv-Q Send-Q Local Address         Foreign Address       State
tcp         0      0 0.0.0.0:22            0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:5432          0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:6379          0.0.0.0:*             LISTEN

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (servers and established)
Proto  Recv-Q Send-Q Local Address         Foreign Address       State
tcp         0      0 0.0.0.0:22            0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:5432          0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:6379          0.0.0.0:*             LISTEN

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (servers and established)
Proto  Recv-Q Send-Q Local Address         Foreign Address       State
tcp         0      0 0.0.0.0:22            0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:5432          0.0.0.0:*             LISTEN
tcp         0      0 0.0.0.0:6379          0.0.0.0:*             LISTEN

```


## Q19 crontab -l
- ATT&CK：T1053 Scheduled Task/Job
- 考點：列出 cron 條目（SALC），或空/無 crontab 訊息（FALC）
- 通過：10/10

### 第 1 次 ✅ SALC
判定：有非空輸出

```
no crontab for root

```

### 第 2 次 ✅ SALC
判定：有非空輸出

```
no crontab for root

```

### 第 3 次 ✅ SALC
判定：有非空輸出

```
no crontab for root

```

### 第 4 次 ✅ SALC
判定：有非空輸出

```
no crontab for root

```

### 第 5 次 ✅ SALC
判定：有非空輸出

```
no crontab for root

```

### 第 6 次 ✅ SALC
判定：有非空輸出

```
no crontab for root

```

### 第 7 次 ✅ SALC
判定：有非空輸出

```
no crontab for root

```

### 第 8 次 ✅ SALC
判定：有非空輸出

```
no crontab for root

```

### 第 9 次 ✅ SALC
判定：有非空輸出

```
no crontab for root

```

### 第 10 次 ✅ SALC
判定：有非空輸出

```
no crontab for root

```


## Q20 cat /etc/os-release
- ATT&CK：T1082 System Information Discovery
- 考點：NAME / VERSION / ID 欄位；須與 uname 宣稱的發行版自洽
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=debian
HOME_URL="https://www.debian.org/"

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=debian
HOME_URL="https://www.debian.org/"

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=debian
HOME_URL="https://www.debian.org/"

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=debian
HOME_URL="https://www.debian.org/"

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=debian
HOME_URL="https://www.debian.org/"

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=debian
HOME_URL="https://www.debian.org/"

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=debian
HOME_URL="https://www.debian.org/"

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=debian
HOME_URL="https://www.debian.org/"

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=debian
HOME_URL="https://www.debian.org/"

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=debian
HOME_URL="https://www.debian.org/"

```


## Q21 ls -la /root
- ATT&CK：T1083 File and Directory Discovery
- 考點：ls -l 格式：權限/連結數/擁有者/群組/大小/日期/名；必有 . 與 .. 目錄項
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 24
drwx------ 2 root  root    4096 Jun 10  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw------- 1 root  root     355 Jun 12  2024 .bash_history
-rw-r--r-- 1 root  root      37 Jun 14  2024 .bashrc
-rw------- 1 root  root      47 Jun 13  2024 .pgpass
-rw-r--r-- 1 root  root      13 Jun 13  2024 .profile

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 24
drwx------ 2 root  root    4096 Jun 10  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw------- 1 root  root     355 Jun 12  2024 .bash_history
-rw-r--r-- 1 root  root      37 Jun 14  2024 .bashrc
-rw------- 1 root  root      47 Jun 13  2024 .pgpass
-rw-r--r-- 1 root  root      13 Jun 13  2024 .profile

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 24
drwx------ 2 root  root    4096 Jun 10  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw------- 1 root  root     355 Jun 12  2024 .bash_history
-rw-r--r-- 1 root  root      37 Jun 14  2024 .bashrc
-rw------- 1 root  root      47 Jun 13  2024 .pgpass
-rw-r--r-- 1 root  root      13 Jun 13  2024 .profile

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 24
drwx------ 2 root  root    4096 Jun 10  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw------- 1 root  root     355 Jun 12  2024 .bash_history
-rw-r--r-- 1 root  root      37 Jun 14  2024 .bashrc
-rw------- 1 root  root      47 Jun 13  2024 .pgpass
-rw-r--r-- 1 root  root      13 Jun 13  2024 .profile

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 24
drwx------ 2 root  root    4096 Jun 10  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw------- 1 root  root     355 Jun 12  2024 .bash_history
-rw-r--r-- 1 root  root      37 Jun 14  2024 .bashrc
-rw------- 1 root  root      47 Jun 13  2024 .pgpass
-rw-r--r-- 1 root  root      13 Jun 13  2024 .profile

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 24
drwx------ 2 root  root    4096 Jun 10  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw------- 1 root  root     355 Jun 12  2024 .bash_history
-rw-r--r-- 1 root  root      37 Jun 14  2024 .bashrc
-rw------- 1 root  root      47 Jun 13  2024 .pgpass
-rw-r--r-- 1 root  root      13 Jun 13  2024 .profile

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 24
drwx------ 2 root  root    4096 Jun 10  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw------- 1 root  root     355 Jun 12  2024 .bash_history
-rw-r--r-- 1 root  root      37 Jun 14  2024 .bashrc
-rw------- 1 root  root      47 Jun 13  2024 .pgpass
-rw-r--r-- 1 root  root      13 Jun 13  2024 .profile

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 24
drwx------ 2 root  root    4096 Jun 10  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw------- 1 root  root     355 Jun 12  2024 .bash_history
-rw-r--r-- 1 root  root      37 Jun 14  2024 .bashrc
-rw------- 1 root  root      47 Jun 13  2024 .pgpass
-rw-r--r-- 1 root  root      13 Jun 13  2024 .profile

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 24
drwx------ 2 root  root    4096 Jun 10  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw------- 1 root  root     355 Jun 12  2024 .bash_history
-rw-r--r-- 1 root  root      37 Jun 14  2024 .bashrc
-rw------- 1 root  root      47 Jun 13  2024 .pgpass
-rw-r--r-- 1 root  root      13 Jun 13  2024 .profile

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 24
drwx------ 2 root  root    4096 Jun 10  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw------- 1 root  root     355 Jun 12  2024 .bash_history
-rw-r--r-- 1 root  root      37 Jun 14  2024 .bashrc
-rw------- 1 root  root      47 Jun 13  2024 .pgpass
-rw-r--r-- 1 root  root      13 Jun 13  2024 .profile

```


## Q22 dmesg | head -10
- ATT&CK：T1082 System Information Discovery
- 考點：核心環形緩衝：[時間戳] 訊息 格式；真機開機訊息序列一致
- 通過：10/10

### 第 1 次 ✅ SALC
判定：有非空輸出

```
dmesg: read kernel buffer failed: Operation not permitted

```

### 第 2 次 ✅ SALC
判定：有非空輸出

```
dmesg: read kernel buffer failed: Operation not permitted

```

### 第 3 次 ✅ SALC
判定：有非空輸出

```
dmesg: read kernel buffer failed: Operation not permitted

```

### 第 4 次 ✅ SALC
判定：有非空輸出

```
dmesg: read kernel buffer failed: Operation not permitted

```

### 第 5 次 ✅ SALC
判定：有非空輸出

```
dmesg: read kernel buffer failed: Operation not permitted

```

### 第 6 次 ✅ SALC
判定：有非空輸出

```
dmesg: read kernel buffer failed: Operation not permitted

```

### 第 7 次 ✅ SALC
判定：有非空輸出

```
dmesg: read kernel buffer failed: Operation not permitted

```

### 第 8 次 ✅ SALC
判定：有非空輸出

```
dmesg: read kernel buffer failed: Operation not permitted

```

### 第 9 次 ✅ SALC
判定：有非空輸出

```
dmesg: read kernel buffer failed: Operation not permitted

```

### 第 10 次 ✅ SALC
判定：有非空輸出

```
dmesg: read kernel buffer failed: Operation not permitted

```


## Q23 cat /proc/meminfo | head -5
- ATT&CK：T1082 System Information Discovery
- 考點：MemTotal/MemFree/MemAvailable 欄位 + kB 單位；數值須與 free -h（Q4）自洽
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:        8167848 kB
MemFree:         5432100 kB
MemAvailable:    6931200 kB
Buffers:          123456 kB
Cached:          1345678 kB

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:        8167848 kB
MemFree:         5432100 kB
MemAvailable:    6931200 kB
Buffers:          123456 kB
Cached:          1345678 kB

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:        8167848 kB
MemFree:         5432100 kB
MemAvailable:    6931200 kB
Buffers:          123456 kB
Cached:          1345678 kB

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:        8167848 kB
MemFree:         5432100 kB
MemAvailable:    6931200 kB
Buffers:          123456 kB
Cached:          1345678 kB

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:        8167848 kB
MemFree:         5432100 kB
MemAvailable:    6931200 kB
Buffers:          123456 kB
Cached:          1345678 kB

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:        8167848 kB
MemFree:         5432100 kB
MemAvailable:    6931200 kB
Buffers:          123456 kB
Cached:          1345678 kB

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:        8167848 kB
MemFree:         5432100 kB
MemAvailable:    6931200 kB
Buffers:          123456 kB
Cached:          1345678 kB

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:        8167848 kB
MemFree:         5432100 kB
MemAvailable:    6931200 kB
Buffers:          123456 kB
Cached:          1345678 kB

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:        8167848 kB
MemFree:         5432100 kB
MemAvailable:    6931200 kB
Buffers:          123456 kB
Cached:          1345678 kB

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:        8167848 kB
MemFree:         5432100 kB
MemAvailable:    6931200 kB
Buffers:          123456 kB
Cached:          1345678 kB

```


## Q24 ls -la /tmp; touch /tmp/probe_marker; ls -la /tmp
- ATT&CK：T1070 Indicator Removal / 狀態一致性
- 考點：touch 後第二次 ls 應出現 probe_marker（考跨命令 FS 狀態）
- 通過：10/10

### 第 1 次 ✅ SALC
判定：有非空輸出

```
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw-r--r-- 1 root  root       0 Jul 21 06:33 probe_marker

```

### 第 2 次 ✅ SALC
判定：有非空輸出

```
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw-r--r-- 1 root  root       0 Jul 21 06:33 probe_marker

```

### 第 3 次 ✅ SALC
判定：有非空輸出

```
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw-r--r-- 1 root  root       0 Jul 21 06:33 probe_marker

```

### 第 4 次 ✅ SALC
判定：有非空輸出

```
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw-r--r-- 1 root  root       0 Jul 21 06:33 probe_marker

```

### 第 5 次 ✅ SALC
判定：有非空輸出

```
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw-r--r-- 1 root  root       0 Jul 21 06:33 probe_marker

```

### 第 6 次 ✅ SALC
判定：有非空輸出

```
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw-r--r-- 1 root  root       0 Jul 21 06:33 probe_marker

```

### 第 7 次 ✅ SALC
判定：有非空輸出

```
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw-r--r-- 1 root  root       0 Jul 21 06:33 probe_marker

```

### 第 8 次 ✅ SALC
判定：有非空輸出

```
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw-r--r-- 1 root  root       0 Jul 21 06:33 probe_marker

```

### 第 9 次 ✅ SALC
判定：有非空輸出

```
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw-r--r-- 1 root  root       0 Jul 21 06:33 probe_marker

```

### 第 10 次 ✅ SALC
判定：有非空輸出

```
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
total 8
drwxrwxrwx 2 root  root    4096 Feb 12  2024 .
drwxr-xr-x 20 root  root    4096 Jun 12  2024 ..
-rw-r--r-- 1 root  root       0 Jul 21 06:33 probe_marker

```


## Q25 hostname
- ATT&CK：T1082 System Information Discovery
- 考點：單行主機名；須與 uname -a（Q1）宣稱的主機名一致
- 通過：10/10

### 第 1 次 ✅ SALC
判定：有非空輸出

```
svr04

```

### 第 2 次 ✅ SALC
判定：有非空輸出

```
svr04

```

### 第 3 次 ✅ SALC
判定：有非空輸出

```
svr04

```

### 第 4 次 ✅ SALC
判定：有非空輸出

```
svr04

```

### 第 5 次 ✅ SALC
判定：有非空輸出

```
svr04

```

### 第 6 次 ✅ SALC
判定：有非空輸出

```
svr04

```

### 第 7 次 ✅ SALC
判定：有非空輸出

```
svr04

```

### 第 8 次 ✅ SALC
判定：有非空輸出

```
svr04

```

### 第 9 次 ✅ SALC
判定：有非空輸出

```
svr04

```

### 第 10 次 ✅ SALC
判定：有非空輸出

```
svr04

```


## Q26 cat /etc/shadow
- ATT&CK：T1003 OS Credential Dumping
- 考點：root 應可讀；格式 user:$hash:... ；或真機式權限錯誤
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$abcXYZ$REDACTED0000000000000000000000000000000000000000000000000000000000000000000000000000:19700:0:99999:7:::
daemon:*:19000:0:99999:7:::
bin:*:19000:0:99999:7:::
sys:*:19000:0:99999:7:::
sshd:!:19000:0:99999:7:::
www-data:*:19000:0:99999:7:::
postgres:!:19000:0:99999:7:::
redis:!:19000:0:99999:7:::
phil:$6$defQWE$EXAMPLE11111111111111111111111111111111111111111111111111111111111111111111111111111:19420:0:99999:7:::
mchen:$6$ghiRTY$EXAMPLE222222222222222222222222222222222222222222222222222222222222222222222222222:19450:0:99999:7:::
deploy:$6$jklUIO$EXAMPLE333333333333333333333333333333333333333333333333333333333333333333333333:19460:0:99999:7:::
svc:!:19420:0:99999:7:::

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$abcXYZ$REDACTED0000000000000000000000000000000000000000000000000000000000000000000000000000:19700:0:99999:7:::
daemon:*:19000:0:99999:7:::
bin:*:19000:0:99999:7:::
sys:*:19000:0:99999:7:::
sshd:!:19000:0:99999:7:::
www-data:*:19000:0:99999:7:::
postgres:!:19000:0:99999:7:::
redis:!:19000:0:99999:7:::
phil:$6$defQWE$EXAMPLE11111111111111111111111111111111111111111111111111111111111111111111111111111:19420:0:99999:7:::
mchen:$6$ghiRTY$EXAMPLE222222222222222222222222222222222222222222222222222222222222222222222222222:19450:0:99999:7:::
deploy:$6$jklUIO$EXAMPLE333333333333333333333333333333333333333333333333333333333333333333333333:19460:0:99999:7:::
svc:!:19420:0:99999:7:::

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$abcXYZ$REDACTED0000000000000000000000000000000000000000000000000000000000000000000000000000:19700:0:99999:7:::
daemon:*:19000:0:99999:7:::
bin:*:19000:0:99999:7:::
sys:*:19000:0:99999:7:::
sshd:!:19000:0:99999:7:::
www-data:*:19000:0:99999:7:::
postgres:!:19000:0:99999:7:::
redis:!:19000:0:99999:7:::
phil:$6$defQWE$EXAMPLE11111111111111111111111111111111111111111111111111111111111111111111111111111:19420:0:99999:7:::
mchen:$6$ghiRTY$EXAMPLE222222222222222222222222222222222222222222222222222222222222222222222222222:19450:0:99999:7:::
deploy:$6$jklUIO$EXAMPLE333333333333333333333333333333333333333333333333333333333333333333333333:19460:0:99999:7:::
svc:!:19420:0:99999:7:::

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$abcXYZ$REDACTED0000000000000000000000000000000000000000000000000000000000000000000000000000:19700:0:99999:7:::
daemon:*:19000:0:99999:7:::
bin:*:19000:0:99999:7:::
sys:*:19000:0:99999:7:::
sshd:!:19000:0:99999:7:::
www-data:*:19000:0:99999:7:::
postgres:!:19000:0:99999:7:::
redis:!:19000:0:99999:7:::
phil:$6$defQWE$EXAMPLE11111111111111111111111111111111111111111111111111111111111111111111111111111:19420:0:99999:7:::
mchen:$6$ghiRTY$EXAMPLE222222222222222222222222222222222222222222222222222222222222222222222222222:19450:0:99999:7:::
deploy:$6$jklUIO$EXAMPLE333333333333333333333333333333333333333333333333333333333333333333333333:19460:0:99999:7:::
svc:!:19420:0:99999:7:::

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$abcXYZ$REDACTED0000000000000000000000000000000000000000000000000000000000000000000000000000:19700:0:99999:7:::
daemon:*:19000:0:99999:7:::
bin:*:19000:0:99999:7:::
sys:*:19000:0:99999:7:::
sshd:!:19000:0:99999:7:::
www-data:*:19000:0:99999:7:::
postgres:!:19000:0:99999:7:::
redis:!:19000:0:99999:7:::
phil:$6$defQWE$EXAMPLE11111111111111111111111111111111111111111111111111111111111111111111111111111:19420:0:99999:7:::
mchen:$6$ghiRTY$EXAMPLE222222222222222222222222222222222222222222222222222222222222222222222222222:19450:0:99999:7:::
deploy:$6$jklUIO$EXAMPLE333333333333333333333333333333333333333333333333333333333333333333333333:19460:0:99999:7:::
svc:!:19420:0:99999:7:::

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$abcXYZ$REDACTED0000000000000000000000000000000000000000000000000000000000000000000000000000:19700:0:99999:7:::
daemon:*:19000:0:99999:7:::
bin:*:19000:0:99999:7:::
sys:*:19000:0:99999:7:::
sshd:!:19000:0:99999:7:::
www-data:*:19000:0:99999:7:::
postgres:!:19000:0:99999:7:::
redis:!:19000:0:99999:7:::
phil:$6$defQWE$EXAMPLE11111111111111111111111111111111111111111111111111111111111111111111111111111:19420:0:99999:7:::
mchen:$6$ghiRTY$EXAMPLE222222222222222222222222222222222222222222222222222222222222222222222222222:19450:0:99999:7:::
deploy:$6$jklUIO$EXAMPLE333333333333333333333333333333333333333333333333333333333333333333333333:19460:0:99999:7:::
svc:!:19420:0:99999:7:::

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$abcXYZ$REDACTED0000000000000000000000000000000000000000000000000000000000000000000000000000:19700:0:99999:7:::
daemon:*:19000:0:99999:7:::
bin:*:19000:0:99999:7:::
sys:*:19000:0:99999:7:::
sshd:!:19000:0:99999:7:::
www-data:*:19000:0:99999:7:::
postgres:!:19000:0:99999:7:::
redis:!:19000:0:99999:7:::
phil:$6$defQWE$EXAMPLE11111111111111111111111111111111111111111111111111111111111111111111111111111:19420:0:99999:7:::
mchen:$6$ghiRTY$EXAMPLE222222222222222222222222222222222222222222222222222222222222222222222222222:19450:0:99999:7:::
deploy:$6$jklUIO$EXAMPLE333333333333333333333333333333333333333333333333333333333333333333333333:19460:0:99999:7:::
svc:!:19420:0:99999:7:::

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$abcXYZ$REDACTED0000000000000000000000000000000000000000000000000000000000000000000000000000:19700:0:99999:7:::
daemon:*:19000:0:99999:7:::
bin:*:19000:0:99999:7:::
sys:*:19000:0:99999:7:::
sshd:!:19000:0:99999:7:::
www-data:*:19000:0:99999:7:::
postgres:!:19000:0:99999:7:::
redis:!:19000:0:99999:7:::
phil:$6$defQWE$EXAMPLE11111111111111111111111111111111111111111111111111111111111111111111111111111:19420:0:99999:7:::
mchen:$6$ghiRTY$EXAMPLE222222222222222222222222222222222222222222222222222222222222222222222222222:19450:0:99999:7:::
deploy:$6$jklUIO$EXAMPLE333333333333333333333333333333333333333333333333333333333333333333333333:19460:0:99999:7:::
svc:!:19420:0:99999:7:::

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$abcXYZ$REDACTED0000000000000000000000000000000000000000000000000000000000000000000000000000:19700:0:99999:7:::
daemon:*:19000:0:99999:7:::
bin:*:19000:0:99999:7:::
sys:*:19000:0:99999:7:::
sshd:!:19000:0:99999:7:::
www-data:*:19000:0:99999:7:::
postgres:!:19000:0:99999:7:::
redis:!:19000:0:99999:7:::
phil:$6$defQWE$EXAMPLE11111111111111111111111111111111111111111111111111111111111111111111111111111:19420:0:99999:7:::
mchen:$6$ghiRTY$EXAMPLE222222222222222222222222222222222222222222222222222222222222222222222222222:19450:0:99999:7:::
deploy:$6$jklUIO$EXAMPLE333333333333333333333333333333333333333333333333333333333333333333333333:19460:0:99999:7:::
svc:!:19420:0:99999:7:::

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$abcXYZ$REDACTED0000000000000000000000000000000000000000000000000000000000000000000000000000:19700:0:99999:7:::
daemon:*:19000:0:99999:7:::
bin:*:19000:0:99999:7:::
sys:*:19000:0:99999:7:::
sshd:!:19000:0:99999:7:::
www-data:*:19000:0:99999:7:::
postgres:!:19000:0:99999:7:::
redis:!:19000:0:99999:7:::
phil:$6$defQWE$EXAMPLE11111111111111111111111111111111111111111111111111111111111111111111111111111:19420:0:99999:7:::
mchen:$6$ghiRTY$EXAMPLE222222222222222222222222222222222222222222222222222222222222222222222222222:19450:0:99999:7:::
deploy:$6$jklUIO$EXAMPLE333333333333333333333333333333333333333333333333333333333333333333333333:19460:0:99999:7:::
svc:!:19420:0:99999:7:::

```


## Q27 w
- ATT&CK：T1033 System Owner/User Discovery
- 考點：表頭 USER TTY FROM LOGIN@ IDLE；登入時間須與模擬時鐘一致
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:32:56 up 7 days,  1:14,  1 user,  load average: 0.08, 0.09, 0.09
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    1.2.3.4          14:32    0.00s  0.05s  0.01s w

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:32:56 up 7 days,  1:14,  1 user,  load average: 0.08, 0.09, 0.09
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    1.2.3.4          14:32    0.00s  0.05s  0.01s w

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:32:56 up 7 days,  1:14,  1 user,  load average: 0.08, 0.09, 0.09
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    1.2.3.4          14:32    0.00s  0.05s  0.01s w

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:32:56 up 7 days,  1:14,  1 user,  load average: 0.08, 0.09, 0.09
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    1.2.3.4          14:32    0.00s  0.05s  0.01s w

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:32:56 up 7 days,  1:14,  1 user,  load average: 0.08, 0.09, 0.09
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    1.2.3.4          14:32    0.00s  0.05s  0.01s w

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:32:56 up 7 days,  1:14,  1 user,  load average: 0.08, 0.09, 0.09
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    1.2.3.4          14:32    0.00s  0.05s  0.01s w

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:32:56 up 7 days,  1:14,  1 user,  load average: 0.08, 0.09, 0.09
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    1.2.3.4          14:32    0.00s  0.05s  0.01s w

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:32:56 up 7 days,  1:14,  1 user,  load average: 0.08, 0.09, 0.09
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    1.2.3.4          14:32    0.00s  0.05s  0.01s w

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:32:56 up 7 days,  1:14,  1 user,  load average: 0.08, 0.09, 0.09
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    1.2.3.4          14:32    0.00s  0.05s  0.01s w

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:32:56 up 7 days,  1:14,  1 user,  load average: 0.08, 0.09, 0.09
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    1.2.3.4          14:32    0.00s  0.05s  0.01s w

```


## Q28 last | head -5
- ATT&CK：T1033 System Owner/User Discovery
- 考點：登入歷史：user tty host 時間範圍；時間須合理且遞減
- 通過：10/10

### 第 1 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:25:48 2026
user     pts/0        1.2.3.4    Sat Jul 22 17:45   still logged in
user     pts/1        1.2.3.4    Fri Jul 21 19:30 - 19:31  (00:01)
user     pts/2        1.2.3.4    Thu Jul 20 20:56 - down   (01:07)

```

### 第 2 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:25:48 2026
user     pts/0        1.2.3.4    Sat Jul 22 17:45   still logged in
user     pts/1        1.2.3.4    Fri Jul 21 19:30 - 19:31  (00:01)
user     pts/2        1.2.3.4    Thu Jul 20 20:56 - down   (01:07)

```

### 第 3 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:25:48 2026
user     pts/0        1.2.3.4    Sat Jul 22 17:45   still logged in
user     pts/1        1.2.3.4    Fri Jul 21 19:30 - 19:31  (00:01)
user     pts/2        1.2.3.4    Thu Jul 20 20:56 - down   (01:07)

```

### 第 4 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:25:48 2026
user     pts/0        1.2.3.4    Sat Jul 22 17:45   still logged in
user     pts/1        1.2.3.4    Fri Jul 21 19:30 - 19:31  (00:01)
user     pts/2        1.2.3.4    Thu Jul 20 20:56 - down   (01:07)

```

### 第 5 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:25:48 2026
user     pts/0        1.2.3.4    Sat Jul 22 17:45   still logged in
user     pts/1        1.2.3.4    Fri Jul 21 19:30 - 19:31  (00:01)
user     pts/2        1.2.3.4    Thu Jul 20 20:56 - down   (01:07)

```

### 第 6 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:25:48 2026
user     pts/0        1.2.3.4    Sat Jul 22 17:45   still logged in
user     pts/1        1.2.3.4    Fri Jul 21 19:30 - 19:31  (00:01)
user     pts/2        1.2.3.4    Thu Jul 20 20:56 - down   (01:07)

```

### 第 7 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:25:48 2026
user     pts/0        1.2.3.4    Sat Jul 22 17:45   still logged in
user     pts/1        1.2.3.4    Fri Jul 21 19:30 - 19:31  (00:01)
user     pts/2        1.2.3.4    Thu Jul 20 20:56 - down   (01:07)

```

### 第 8 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:25:48 2026
user     pts/0        1.2.3.4    Sat Jul 22 17:45   still logged in
user     pts/1        1.2.3.4    Fri Jul 21 19:30 - 19:31  (00:01)
user     pts/2        1.2.3.4    Thu Jul 20 20:56 - down   (01:07)

```

### 第 9 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:25:48 2026
user     pts/0        1.2.3.4    Sat Jul 22 17:45   still logged in
user     pts/1        1.2.3.4    Fri Jul 21 19:30 - 19:31  (00:01)
user     pts/2        1.2.3.4    Thu Jul 20 20:56 - down   (01:07)

```

### 第 10 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:25:48 2026
user     pts/0        1.2.3.4    Sat Jul 22 17:45   still logged in
user     pts/1        1.2.3.4    Fri Jul 21 19:30 - 19:31  (00:01)
user     pts/2        1.2.3.4    Thu Jul 20 20:56 - down   (01:07)

```


## Q29 cat /proc/version
- ATT&CK：T1082 System Information Discovery
- 考點：核心版本字串；須與 uname -a（Q1）的 kernel 版本完全一致
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-kernel)

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-kernel)

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-kernel)

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-kernel)

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-kernel)

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-kernel)

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-kernel)

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-kernel)

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-kernel)

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-kernel)

```


## Q30 sudo -l
- ATT&CK：T1069 Permission Groups Discovery
- 考點：列出 sudo 權限；root 應顯示 (ALL) ALL 或類似
- 通過：10/10

### 第 1 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on svr04:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User root may run the following commands on svr04:
    (ALL : ALL) ALL

```

### 第 2 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on svr04:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User root may run the following commands on svr04:
    (ALL : ALL) ALL

```

### 第 3 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on svr04:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User root may run the following commands on svr04:
    (ALL : ALL) ALL

```

### 第 4 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on svr04:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User root may run the following commands on svr04:
    (ALL : ALL) ALL

```

### 第 5 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on svr04:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User root may run the following commands on svr04:
    (ALL : ALL) ALL

```

### 第 6 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on svr04:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User root may run the following commands on svr04:
    (ALL : ALL) ALL

```

### 第 7 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on svr04:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User root may run the following commands on svr04:
    (ALL : ALL) ALL

```

### 第 8 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on svr04:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User root may run the following commands on svr04:
    (ALL : ALL) ALL

```

### 第 9 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on svr04:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User root may run the following commands on svr04:
    (ALL : ALL) ALL

```

### 第 10 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on svr04:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User root may run the following commands on svr04:
    (ALL : ALL) ALL

```
