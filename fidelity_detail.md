# 擬真度細項（每題 10 次）


## Q1 uname -a
- ATT&CK：T1082 System Information Discovery
- 考點：格式擬真：核心資訊欄位順序（kernel name / hostname / release / version / machine）齊全且順序正確
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux happydog 5.10.0-19-amd64 #1 SMP Debian 5.10.178-2 (2023-05-16) x86_64 GNU/Linux
```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux happydog 5.10.0-19-amd64 #1 SMP Debian 5.10.178-2 (2023-05-16) x86_64 GNU/Linux
```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux happydog 5.10.0-19-amd64 #1 SMP Debian 5.10.178-2 (2023-05-16) x86_64 GNU/Linux
```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux happydog 5.10.0-19-amd64 #1 SMP Debian 5.10.178-2 (2023-05-16) x86_64 GNU/Linux
```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux happydog 5.10.0-19-amd64 #1 SMP Debian 5.10.178-2 (2023-05-16) x86_64 GNU/Linux
```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux happydog 5.10.0-19-amd64 #1 SMP Debian 5.10.178-2 (2023-05-16) x86_64 GNU/Linux
```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux happydog 5.10.0-19-amd64 #1 SMP Debian 5.10.178-2 (2023-05-16) x86_64 GNU/Linux
```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux happydog 5.10.0-19-amd64 #1 SMP Debian 5.10.178-2 (2023-05-16) x86_64 GNU/Linux
```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux happydog 5.10.0-19-amd64 #1 SMP Debian 5.10.178-2 (2023-05-16) x86_64 GNU/Linux
```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux happydog 5.10.0-19-amd64 #1 SMP Debian 5.10.178-2 (2023-05-16) x86_64 GNU/Linux
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
model		: 62
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0x70c
cpu MHz		: 2399.998
cache size	: 45088 KB
physical id	: 0
siblings	: 4
core id		: 0
cpu cores	: 16
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb intel_pt ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm mpx rdseed adx smap clflushopt intel_ctxsw xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp pku ospke md_clear flush_l1d
bugs		: spectre_v1 spectre_v2 spec_store_bypass swapgs itlb_multihit l1tf mds swapgs_itlb_smt racing_ts retbleed
bogomips	: 4800.00
cpu implementer	: 0x51
(cpu architecture: 7)
cpu variant		: 0x1
cpu part		: 0xd0f
cpu revision		: 0x2
Hardware		: x86_64

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 62
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0x70c
cpu MHz		: 2399.998
cache size	: 45088 KB
physical id	: 0
siblings	: 4
core id		: 0
cpu cores	: 16
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb intel_pt ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm mpx rdseed adx smap clflushopt intel_ctxsw xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp pku ospke md_clear flush_l1d
bugs		: spectre_v1 spectre_v2 spec_store_bypass swapgs itlb_multihit l1tf mds swapgs_itlb_smt racing_ts retbleed
bogomips	: 4800.00
cpu implementer	: 0x51
(cpu architecture: 7)
cpu variant		: 0x1
cpu part		: 0xd0f
cpu revision		: 0x2
Hardware		: x86_64

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 62
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0x70c
cpu MHz		: 2399.998
cache size	: 45088 KB
physical id	: 0
siblings	: 4
core id		: 0
cpu cores	: 16
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb intel_pt ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm mpx rdseed adx smap clflushopt intel_ctxsw xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp pku ospke md_clear flush_l1d
bugs		: spectre_v1 spectre_v2 spec_store_bypass swapgs itlb_multihit l1tf mds swapgs_itlb_smt racing_ts retbleed
bogomips	: 4800.00
cpu implementer	: 0x51
(cpu architecture: 7)
cpu variant		: 0x1
cpu part		: 0xd0f
cpu revision		: 0x2
Hardware		: x86_64

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 62
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0x70c
cpu MHz		: 2399.998
cache size	: 45088 KB
physical id	: 0
siblings	: 4
core id		: 0
cpu cores	: 16
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb intel_pt ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm mpx rdseed adx smap clflushopt intel_ctxsw xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp pku ospke md_clear flush_l1d
bugs		: spectre_v1 spectre_v2 spec_store_bypass swapgs itlb_multihit l1tf mds swapgs_itlb_smt racing_ts retbleed
bogomips	: 4800.00
cpu implementer	: 0x51
(cpu architecture: 7)
cpu variant		: 0x1
cpu part		: 0xd0f
cpu revision		: 0x2
Hardware		: x86_64

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 62
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0x70c
cpu MHz		: 2399.998
cache size	: 45088 KB
physical id	: 0
siblings	: 4
core id		: 0
cpu cores	: 16
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb intel_pt ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm mpx rdseed adx smap clflushopt intel_ctxsw xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp pku ospke md_clear flush_l1d
bugs		: spectre_v1 spectre_v2 spec_store_bypass swapgs itlb_multihit l1tf mds swapgs_itlb_smt racing_ts retbleed
bogomips	: 4800.00
cpu implementer	: 0x51
(cpu architecture: 7)
cpu variant		: 0x1
cpu part		: 0xd0f
cpu revision		: 0x2
Hardware		: x86_64

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 62
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0x70c
cpu MHz		: 2399.998
cache size	: 45088 KB
physical id	: 0
siblings	: 4
core id		: 0
cpu cores	: 16
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb intel_pt ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm mpx rdseed adx smap clflushopt intel_ctxsw xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp pku ospke md_clear flush_l1d
bugs		: spectre_v1 spectre_v2 spec_store_bypass swapgs itlb_multihit l1tf mds swapgs_itlb_smt racing_ts retbleed
bogomips	: 4800.00
cpu implementer	: 0x51
(cpu architecture: 7)
cpu variant		: 0x1
cpu part		: 0xd0f
cpu revision		: 0x2
Hardware		: x86_64

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 62
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0x70c
cpu MHz		: 2399.998
cache size	: 45088 KB
physical id	: 0
siblings	: 4
core id		: 0
cpu cores	: 16
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb intel_pt ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm mpx rdseed adx smap clflushopt intel_ctxsw xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp pku ospke md_clear flush_l1d
bugs		: spectre_v1 spectre_v2 spec_store_bypass swapgs itlb_multihit l1tf mds swapgs_itlb_smt racing_ts retbleed
bogomips	: 4800.00
cpu implementer	: 0x51
(cpu architecture: 7)
cpu variant		: 0x1
cpu part		: 0xd0f
cpu revision		: 0x2
Hardware		: x86_64

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 62
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0x70c
cpu MHz		: 2399.998
cache size	: 45088 KB
physical id	: 0
siblings	: 4
core id		: 0
cpu cores	: 16
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb intel_pt ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm mpx rdseed adx smap clflushopt intel_ctxsw xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp pku ospke md_clear flush_l1d
bugs		: spectre_v1 spectre_v2 spec_store_bypass swapgs itlb_multihit l1tf mds swapgs_itlb_smt racing_ts retbleed
bogomips	: 4800.00
cpu implementer	: 0x51
(cpu architecture: 7)
cpu variant		: 0x1
cpu part		: 0xd0f
cpu revision		: 0x2
Hardware		: x86_64

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 62
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0x70c
cpu MHz		: 2399.998
cache size	: 45088 KB
physical id	: 0
siblings	: 4
core id		: 0
cpu cores	: 16
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb intel_pt ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm mpx rdseed adx smap clflushopt intel_ctxsw xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp pku ospke md_clear flush_l1d
bugs		: spectre_v1 spectre_v2 spec_store_bypass swapgs itlb_multihit l1tf mds swapgs_itlb_smt racing_ts retbleed
bogomips	: 4800.00
cpu implementer	: 0x51
(cpu architecture: 7)
cpu variant		: 0x1
cpu part		: 0xd0f
cpu revision		: 0x2
Hardware		: x86_64

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
processor	: 0
vendor_id	: GenuineIntel
cpu family	: 6
model		: 62
model name	: Intel(R) Xeon(R) CPU E5-2680 v4 @ 2.40GHz
stepping	: 1
microcode	: 0x70c
cpu MHz		: 2399.998
cache size	: 45088 KB
physical id	: 0
siblings	: 4
core id		: 0
cpu cores	: 16
apicid		: 0
initial apicid	: 0
fpu		: yes
fpu_exception	: yes
cpuid level	: 20
wp		: yes
flags		: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc arch_perfmon nopl xtopology nonstop_tsc cpuid aperfmperf tsc_known_freq pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch epb intel_pt ssbd ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid fsgsbase tsc_adjust bmi1 hle avx2 smep bmi2 erms invpcid rtm mpx rdseed adx smap clflushopt intel_ctxsw xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp pku ospke md_clear flush_l1d
bugs		: spectre_v1 spectre_v2 spec_store_bypass swapgs itlb_multihit l1tf mds swapgs_itlb_smt racing_ts retbleed
bogomips	: 4800.00
cpu implementer	: 0x51
(cpu architecture: 7)
cpu variant		: 0x1
cpu part		: 0xd0f
cpu revision		: 0x2
Hardware		: x86_64

```


## Q3 cat /proc/cpuinfo | grep 'model name' | head -1 | awk '{print $4}'
- ATT&CK：T1082 System Information Discovery
- 考點：跨工具管線一致性：cat→grep→awk 串起來，最終欄位提取結果須與 Q2 的 model name 欄位自洽（考狀態/邏輯一致，非各自亂生）
- 通過：10/10

### 第 1 次 ✅ SALC
判定：有非空輸出

```
Intel(R) Xeon(R) CPU E5-2680 v4
```

### 第 2 次 ✅ SALC
判定：有非空輸出

```
Intel(R) Xeon(R) CPU E5-2680 v4
```

### 第 3 次 ✅ SALC
判定：有非空輸出

```
Intel(R) Xeon(R) CPU E5-2680 v4
```

### 第 4 次 ✅ SALC
判定：有非空輸出

```
Intel(R) Xeon(R) CPU E5-2680 v4
```

### 第 5 次 ✅ SALC
判定：有非空輸出

```
Intel(R) Xeon(R) CPU E5-2680 v4
```

### 第 6 次 ✅ SALC
判定：有非空輸出

```
Intel(R) Xeon(R) CPU E5-2680 v4
```

### 第 7 次 ✅ SALC
判定：有非空輸出

```
Intel(R) Xeon(R) CPU E5-2680 v4
```

### 第 8 次 ✅ SALC
判定：有非空輸出

```
Intel(R) Xeon(R) CPU E5-2680 v4
```

### 第 9 次 ✅ SALC
判定：有非空輸出

```
Intel(R) Xeon(R) CPU E5-2680 v4
```

### 第 10 次 ✅ SALC
判定：有非空輸出

```
Intel(R) Xeon(R) CPU E5-2680 v4
```


## Q4 free -h
- ATT&CK：T1082 System Information Discovery
- 考點：表頭與欄位格式：total/used/free/shared/buff/cache/available 欄位齊全，Mem: 與 Swap: 兩列，帶人類可讀單位
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
              total        used        free      shared  buff/cache   available
Mem:           7.8G        2.3G        1.5G         96M        4.0G        4.4G
Swap:            0B          0B          0B
```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
              total        used        free      shared  buff/cache   available
Mem:           7.8G        2.3G        1.5G         96M        4.0G        4.4G
Swap:            0B          0B          0B
```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
              total        used        free      shared  buff/cache   available
Mem:           7.8G        2.3G        1.5G         96M        4.0G        4.4G
Swap:            0B          0B          0B
```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
              total        used        free      shared  buff/cache   available
Mem:           7.8G        2.3G        1.5G         96M        4.0G        4.4G
Swap:            0B          0B          0B
```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
              total        used        free      shared  buff/cache   available
Mem:           7.8G        2.3G        1.5G         96M        4.0G        4.4G
Swap:            0B          0B          0B
```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
              total        used        free      shared  buff/cache   available
Mem:           7.8G        2.3G        1.5G         96M        4.0G        4.4G
Swap:            0B          0B          0B
```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
              total        used        free      shared  buff/cache   available
Mem:           7.8G        2.3G        1.5G         96M        4.0G        4.4G
Swap:            0B          0B          0B
```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
              total        used        free      shared  buff/cache   available
Mem:           7.8G        2.3G        1.5G         96M        4.0G        4.4G
Swap:            0B          0B          0B
```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
              total        used        free      shared  buff/cache   available
Mem:           7.8G        2.3G        1.5G         96M        4.0G        4.4G
Swap:            0B          0B          0B
```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
              total        used        free      shared  buff/cache   available
Mem:           7.8G        2.3G        1.5G         96M        4.0G        4.4G
Swap:            0B          0B          0B
```


## Q5 ip addr
- ATT&CK：T1016 System Network Configuration Discovery
- 考點：介面/位址格式：至少 lo + 一個實體介面，含 inet 行、MAC（link/ether）、編號前綴（1: 2:）
- 通過：0/10

### 第 1 次 ❌ SALNLC
判定：行首雜訊（LLM 生成殘渣）：'c       v'

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
c       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0c:29:4d:8b:67 brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.103/24 brdisc 192.168.56.2 scope global ens33
c       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe4d:8b67/64 scope link 
       valid_lft forever preferred_lft forever
```

### 第 2 次 ❌ SALNLC
判定：行首雜訊（LLM 生成殘渣）：'c       v'

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
c       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0c:29:4d:8b:67 brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.103/24 brdisc 192.168.56.2 scope global ens33
c       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe4d:8b67/64 scope link 
       valid_lft forever preferred_lft forever
```

### 第 3 次 ❌ SALNLC
判定：行首雜訊（LLM 生成殘渣）：'c       v'

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
c       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0c:29:4d:8b:67 brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.103/24 brdisc 192.168.56.2 scope global ens33
c       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe4d:8b67/64 scope link 
       valid_lft forever preferred_lft forever
```

### 第 4 次 ❌ SALNLC
判定：行首雜訊（LLM 生成殘渣）：'c       v'

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
c       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0c:29:4d:8b:67 brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.103/24 brdisc 192.168.56.2 scope global ens33
c       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe4d:8b67/64 scope link 
       valid_lft forever preferred_lft forever
```

### 第 5 次 ❌ SALNLC
判定：行首雜訊（LLM 生成殘渣）：'c       v'

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
c       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0c:29:4d:8b:67 brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.103/24 brdisc 192.168.56.2 scope global ens33
c       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe4d:8b67/64 scope link 
       valid_lft forever preferred_lft forever
```

### 第 6 次 ❌ SALNLC
判定：行首雜訊（LLM 生成殘渣）：'c       v'

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
c       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0c:29:4d:8b:67 brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.103/24 brdisc 192.168.56.2 scope global ens33
c       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe4d:8b67/64 scope link 
       valid_lft forever preferred_lft forever
```

### 第 7 次 ❌ SALNLC
判定：行首雜訊（LLM 生成殘渣）：'c       v'

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
c       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0c:29:4d:8b:67 brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.103/24 brdisc 192.168.56.2 scope global ens33
c       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe4d:8b67/64 scope link 
       valid_lft forever preferred_lft forever
```

### 第 8 次 ❌ SALNLC
判定：行首雜訊（LLM 生成殘渣）：'c       v'

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
c       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0c:29:4d:8b:67 brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.103/24 brdisc 192.168.56.2 scope global ens33
c       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe4d:8b67/64 scope link 
       valid_lft forever preferred_lft forever
```

### 第 9 次 ❌ SALNLC
判定：行首雜訊（LLM 生成殘渣）：'c       v'

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
c       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0c:29:4d:8b:67 brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.103/24 brdisc 192.168.56.2 scope global ens33
c       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe4d:8b67/64 scope link 
       valid_lft forever preferred_lft forever
```

### 第 10 次 ❌ SALNLC
判定：行首雜訊（LLM 生成殘渣）：'c       v'

```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
c       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens33: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0c:29:4d:8b:67 brd ff:ff:ff:ff:ff:ff
    inet 192.168.56.103/24 brdisc 192.168.56.2 scope global ens33
c       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe4d:8b67/64 scope link 
       valid_lft forever preferred_lft forever
```


## Q6 cat /etc/resolv.conf
- ATT&CK：T1016 System Network Configuration Discovery
- 考點：檔案內容擬真：nameserver 行格式正確
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
nameserver 8.8.8.8
nameserver 8.8.4.4
search example.com
```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
nameserver 8.8.8.8
nameserver 8.8.4.4
search example.com
```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
nameserver 8.8.8.8
nameserver 8.8.4.4
search example.com
```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
nameserver 8.8.8.8
nameserver 8.8.4.4
search example.com
```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
nameserver 8.8.8.8
nameserver 8.8.4.4
search example.com
```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
nameserver 8.8.8.8
nameserver 8.8.4.4
search example.com
```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
nameserver 8.8.8.8
nameserver 8.8.4.4
search example.com
```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
nameserver 8.8.8.8
nameserver 8.8.4.4
search example.com
```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
nameserver 8.8.8.8
nameserver 8.8.4.4
search example.com
```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
nameserver 8.8.8.8
nameserver 8.8.4.4
search example.com
```


## Q7 ps aux | head -5
- ATT&CK：T1057 Process Discovery
- 考點：表頭欄位順序：USER PID %CPU %MEM VSZ RSS TTY STAT START TIME COMMAND；且第一列通常是 root 的 PID 1
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  29848  3760 ?        Ss  Jul14   0:05 /sbin/init
root       28  0.0  0.0      0     0 ?        S    Jul14   0:00 [kthreadd]
root       36  0.0  0.0      0     0 ?        I<   Jul14   0:00 [rcu_gp]
```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  29848  3760 ?        Ss  Jul14   0:05 /sbin/init
root       28  0.0  0.0      0     0 ?        S    Jul14   0:00 [kthreadd]
root       36  0.0  0.0      0     0 ?        I<   Jul14   0:00 [rcu_gp]
```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  29848  3760 ?        Ss  Jul14   0:05 /sbin/init
root       28  0.0  0.0      0     0 ?        S    Jul14   0:00 [kthreadd]
root       36  0.0  0.0      0     0 ?        I<   Jul14   0:00 [rcu_gp]
```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  29848  3760 ?        Ss  Jul14   0:05 /sbin/init
root       28  0.0  0.0      0     0 ?        S    Jul14   0:00 [kthreadd]
root       36  0.0  0.0      0     0 ?        I<   Jul14   0:00 [rcu_gp]
```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  29848  3760 ?        Ss  Jul14   0:05 /sbin/init
root       28  0.0  0.0      0     0 ?        S    Jul14   0:00 [kthreadd]
root       36  0.0  0.0      0     0 ?        I<   Jul14   0:00 [rcu_gp]
```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  29848  3760 ?        Ss  Jul14   0:05 /sbin/init
root       28  0.0  0.0      0     0 ?        S    Jul14   0:00 [kthreadd]
root       36  0.0  0.0      0     0 ?        I<   Jul14   0:00 [rcu_gp]
```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  29848  3760 ?        Ss  Jul14   0:05 /sbin/init
root       28  0.0  0.0      0     0 ?        S    Jul14   0:00 [kthreadd]
root       36  0.0  0.0      0     0 ?        I<   Jul14   0:00 [rcu_gp]
```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  29848  3760 ?        Ss  Jul14   0:05 /sbin/init
root       28  0.0  0.0      0     0 ?        S    Jul14   0:00 [kthreadd]
root       36  0.0  0.0      0     0 ?        I<   Jul14   0:00 [rcu_gp]
```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  29848  3760 ?        Ss  Jul14   0:05 /sbin/init
root       28  0.0  0.0      0     0 ?        S    Jul14   0:00 [kthreadd]
root       36  0.0  0.0      0     0 ?        I<   Jul14   0:00 [rcu_gp]
```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.0  29848  3760 ?        Ss  Jul14   0:05 /sbin/init
root       28  0.0  0.0      0     0 ?        S    Jul14   0:00 [kthreadd]
root       36  0.0  0.0      0     0 ?        I<   Jul14   0:00 [rcu_gp]
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
- 通過：0/10

### 第 1 次 ❌ SALNLC
判定：幻覺掛載點（真機不存在）：'/dev/.mapper'

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime,seclabel)
systemd-1 on /proc/sys/kernel/config type configfs (rw,relatime)
device-mapper on /dev/.mapper type autofs (rw,relatime,fd=28,pgrp=796,timeout=300,minproto=5,maxproto=5,direct,seclabel)
bpf on /sys/fs/bpf type bpf (rw,nosuid,nodev,noexec,relatime,mode=7000)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
systemd-1 on /run/systemd/resolve type automount (rw,relatime,fallback=host,seclabel)
systemd-1 on /run/systemd/sessions type automount (rw,relatime,fallback=tmpfs,seclabel)
```

### 第 2 次 ❌ SALNLC
判定：幻覺掛載點（真機不存在）：'/dev/.mapper'

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime,seclabel)
systemd-1 on /proc/sys/kernel/config type configfs (rw,relatime)
device-mapper on /dev/.mapper type autofs (rw,relatime,fd=28,pgrp=796,timeout=300,minproto=5,maxproto=5,direct,seclabel)
bpf on /sys/fs/bpf type bpf (rw,nosuid,nodev,noexec,relatime,mode=7000)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
systemd-1 on /run/systemd/resolve type automount (rw,relatime,fallback=host,seclabel)
systemd-1 on /run/systemd/sessions type automount (rw,relatime,fallback=tmpfs,seclabel)
```

### 第 3 次 ❌ SALNLC
判定：幻覺掛載點（真機不存在）：'/dev/.mapper'

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime,seclabel)
systemd-1 on /proc/sys/kernel/config type configfs (rw,relatime)
device-mapper on /dev/.mapper type autofs (rw,relatime,fd=28,pgrp=796,timeout=300,minproto=5,maxproto=5,direct,seclabel)
bpf on /sys/fs/bpf type bpf (rw,nosuid,nodev,noexec,relatime,mode=7000)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
systemd-1 on /run/systemd/resolve type automount (rw,relatime,fallback=host,seclabel)
systemd-1 on /run/systemd/sessions type automount (rw,relatime,fallback=tmpfs,seclabel)
```

### 第 4 次 ❌ SALNLC
判定：幻覺掛載點（真機不存在）：'/dev/.mapper'

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime,seclabel)
systemd-1 on /proc/sys/kernel/config type configfs (rw,relatime)
device-mapper on /dev/.mapper type autofs (rw,relatime,fd=28,pgrp=796,timeout=300,minproto=5,maxproto=5,direct,seclabel)
bpf on /sys/fs/bpf type bpf (rw,nosuid,nodev,noexec,relatime,mode=7000)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
systemd-1 on /run/systemd/resolve type automount (rw,relatime,fallback=host,seclabel)
systemd-1 on /run/systemd/sessions type automount (rw,relatime,fallback=tmpfs,seclabel)
```

### 第 5 次 ❌ SALNLC
判定：幻覺掛載點（真機不存在）：'/dev/.mapper'

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime,seclabel)
systemd-1 on /proc/sys/kernel/config type configfs (rw,relatime)
device-mapper on /dev/.mapper type autofs (rw,relatime,fd=28,pgrp=796,timeout=300,minproto=5,maxproto=5,direct,seclabel)
bpf on /sys/fs/bpf type bpf (rw,nosuid,nodev,noexec,relatime,mode=7000)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
systemd-1 on /run/systemd/resolve type automount (rw,relatime,fallback=host,seclabel)
systemd-1 on /run/systemd/sessions type automount (rw,relatime,fallback=tmpfs,seclabel)
```

### 第 6 次 ❌ SALNLC
判定：幻覺掛載點（真機不存在）：'/dev/.mapper'

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime,seclabel)
systemd-1 on /proc/sys/kernel/config type configfs (rw,relatime)
device-mapper on /dev/.mapper type autofs (rw,relatime,fd=28,pgrp=796,timeout=300,minproto=5,maxproto=5,direct,seclabel)
bpf on /sys/fs/bpf type bpf (rw,nosuid,nodev,noexec,relatime,mode=7000)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
systemd-1 on /run/systemd/resolve type automount (rw,relatime,fallback=host,seclabel)
systemd-1 on /run/systemd/sessions type automount (rw,relatime,fallback=tmpfs,seclabel)
```

### 第 7 次 ❌ SALNLC
判定：幻覺掛載點（真機不存在）：'/dev/.mapper'

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime,seclabel)
systemd-1 on /proc/sys/kernel/config type configfs (rw,relatime)
device-mapper on /dev/.mapper type autofs (rw,relatime,fd=28,pgrp=796,timeout=300,minproto=5,maxproto=5,direct,seclabel)
bpf on /sys/fs/bpf type bpf (rw,nosuid,nodev,noexec,relatime,mode=7000)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
systemd-1 on /run/systemd/resolve type automount (rw,relatime,fallback=host,seclabel)
systemd-1 on /run/systemd/sessions type automount (rw,relatime,fallback=tmpfs,seclabel)
```

### 第 8 次 ❌ SALNLC
判定：幻覺掛載點（真機不存在）：'/dev/.mapper'

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime,seclabel)
systemd-1 on /proc/sys/kernel/config type configfs (rw,relatime)
device-mapper on /dev/.mapper type autofs (rw,relatime,fd=28,pgrp=796,timeout=300,minproto=5,maxproto=5,direct,seclabel)
bpf on /sys/fs/bpf type bpf (rw,nosuid,nodev,noexec,relatime,mode=7000)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
systemd-1 on /run/systemd/resolve type automount (rw,relatime,fallback=host,seclabel)
systemd-1 on /run/systemd/sessions type automount (rw,relatime,fallback=tmpfs,seclabel)
```

### 第 9 次 ❌ SALNLC
判定：幻覺掛載點（真機不存在）：'/dev/.mapper'

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime,seclabel)
systemd-1 on /proc/sys/kernel/config type configfs (rw,relatime)
device-mapper on /dev/.mapper type autofs (rw,relatime,fd=28,pgrp=796,timeout=300,minproto=5,maxproto=5,direct,seclabel)
bpf on /sys/fs/bpf type bpf (rw,nosuid,nodev,noexec,relatime,mode=7000)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
systemd-1 on /run/systemd/resolve type automount (rw,relatime,fallback=host,seclabel)
systemd-1 on /run/systemd/sessions type automount (rw,relatime,fallback=tmpfs,seclabel)
```

### 第 10 次 ❌ SALNLC
判定：幻覺掛載點（真機不存在）：'/dev/.mapper'

```
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime,seclabel)
systemd-1 on /proc/sys/kernel/config type configfs (rw,relatime)
device-mapper on /dev/.mapper type autofs (rw,relatime,fd=28,pgrp=796,timeout=300,minproto=5,maxproto=5,direct,seclabel)
bpf on /sys/fs/bpf type bpf (rw,nosuid,nodev,noexec,relatime,mode=7000)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
systemd-1 on /run/systemd/resolve type automount (rw,relatime,fallback=host,seclabel)
systemd-1 on /run/systemd/sessions type automount (rw,relatime,fallback=tmpfs,seclabel)
```


## Q10 date +%s; sleep 2; date +%s
- ATT&CK：T1497 Virtualization/Sandbox Evasion
- 考點：跨命令狀態一致性（§6 process model）：第二個時間戳應比第一個大約 2（±1）。考蜜罐能否維持時間流動一致，而非兩次憑空生成無關數字。這是 easypot 單命令無狀態設計最可能輸的題。
- 通過：0/10

### 第 1 次 ❌ SALNLC
判定：時間戳差 0s，非真機的 ~2s（狀態不一致）

```
1795286071
1795286071
```

### 第 2 次 ❌ SALNLC
判定：時間戳差 0s，非真機的 ~2s（狀態不一致）

```
1795286071
1795286071
```

### 第 3 次 ❌ SALNLC
判定：時間戳差 0s，非真機的 ~2s（狀態不一致）

```
1795286071
1795286071
```

### 第 4 次 ❌ SALNLC
判定：時間戳差 0s，非真機的 ~2s（狀態不一致）

```
1795286071
1795286071
```

### 第 5 次 ❌ SALNLC
判定：時間戳差 0s，非真機的 ~2s（狀態不一致）

```
1795286071
1795286071
```

### 第 6 次 ❌ SALNLC
判定：時間戳差 0s，非真機的 ~2s（狀態不一致）

```
1795286071
1795286071
```

### 第 7 次 ❌ SALNLC
判定：時間戳差 0s，非真機的 ~2s（狀態不一致）

```
1795286071
1795286071
```

### 第 8 次 ❌ SALNLC
判定：時間戳差 0s，非真機的 ~2s（狀態不一致）

```
1795286071
1795286071
```

### 第 9 次 ❌ SALNLC
判定：時間戳差 0s，非真機的 ~2s（狀態不一致）

```
1795286071
1795286071
```

### 第 10 次 ❌ SALNLC
判定：時間戳差 0s，非真機的 ~2s（狀態不一致）

```
1795286071
1795286071
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
 21:15  up 7 days, 3:16,  4 users,  load average: 0.08, 0.09, 0.08
```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 21:15  up 7 days, 3:16,  4 users,  load average: 0.08, 0.09, 0.08
```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 21:15  up 7 days, 3:16,  4 users,  load average: 0.08, 0.09, 0.08
```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 21:15  up 7 days, 3:16,  4 users,  load average: 0.08, 0.09, 0.08
```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 21:15  up 7 days, 3:16,  4 users,  load average: 0.08, 0.09, 0.08
```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 21:15  up 7 days, 3:16,  4 users,  load average: 0.08, 0.09, 0.08
```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 21:15  up 7 days, 3:16,  4 users,  load average: 0.08, 0.09, 0.08
```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 21:15  up 7 days, 3:16,  4 users,  load average: 0.08, 0.09, 0.08
```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 21:15  up 7 days, 3:16,  4 users,  load average: 0.08, 0.09, 0.08
```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 21:15  up 7 days, 3:16,  4 users,  load average: 0.08, 0.09, 0.08
```


## Q15 df -h
- ATT&CK：T1082 System Information Discovery
- 考點：表頭 Filesystem Size Used Avail Use% Mounted；必有根 / 掛載列
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem      Size  Used Avail Use% Mounted on
udev            3.9G     0  3.9G   0% /dev
tmpfs           785M  1.6M  784M   1% /run
/dev/sda2        20G  4.1G   16G  21% /
none            4.0K     0  4.0K   0% /sys/fs/cgroup
tmpfs           3.9G  8.0K  3.9G   1% /tmp
/dev/sda1       256M   72M  185M  28% /boot
none            4.0K     0  4.0K   0% /run/lock
none            3.9G     0  3.9G   0% /sys/fs/bpf
tmpfs           785M     0  785M   0% /run/user/1000
```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem      Size  Used Avail Use% Mounted on
udev            3.9G     0  3.9G   0% /dev
tmpfs           785M  1.6M  784M   1% /run
/dev/sda2        20G  4.1G   16G  21% /
none            4.0K     0  4.0K   0% /sys/fs/cgroup
tmpfs           3.9G  8.0K  3.9G   1% /tmp
/dev/sda1       256M   72M  185M  28% /boot
none            4.0K     0  4.0K   0% /run/lock
none            3.9G     0  3.9G   0% /sys/fs/bpf
tmpfs           785M     0  785M   0% /run/user/1000
```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem      Size  Used Avail Use% Mounted on
udev            3.9G     0  3.9G   0% /dev
tmpfs           785M  1.6M  784M   1% /run
/dev/sda2        20G  4.1G   16G  21% /
none            4.0K     0  4.0K   0% /sys/fs/cgroup
tmpfs           3.9G  8.0K  3.9G   1% /tmp
/dev/sda1       256M   72M  185M  28% /boot
none            4.0K     0  4.0K   0% /run/lock
none            3.9G     0  3.9G   0% /sys/fs/bpf
tmpfs           785M     0  785M   0% /run/user/1000
```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem      Size  Used Avail Use% Mounted on
udev            3.9G     0  3.9G   0% /dev
tmpfs           785M  1.6M  784M   1% /run
/dev/sda2        20G  4.1G   16G  21% /
none            4.0K     0  4.0K   0% /sys/fs/cgroup
tmpfs           3.9G  8.0K  3.9G   1% /tmp
/dev/sda1       256M   72M  185M  28% /boot
none            4.0K     0  4.0K   0% /run/lock
none            3.9G     0  3.9G   0% /sys/fs/bpf
tmpfs           785M     0  785M   0% /run/user/1000
```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem      Size  Used Avail Use% Mounted on
udev            3.9G     0  3.9G   0% /dev
tmpfs           785M  1.6M  784M   1% /run
/dev/sda2        20G  4.1G   16G  21% /
none            4.0K     0  4.0K   0% /sys/fs/cgroup
tmpfs           3.9G  8.0K  3.9G   1% /tmp
/dev/sda1       256M   72M  185M  28% /boot
none            4.0K     0  4.0K   0% /run/lock
none            3.9G     0  3.9G   0% /sys/fs/bpf
tmpfs           785M     0  785M   0% /run/user/1000
```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem      Size  Used Avail Use% Mounted on
udev            3.9G     0  3.9G   0% /dev
tmpfs           785M  1.6M  784M   1% /run
/dev/sda2        20G  4.1G   16G  21% /
none            4.0K     0  4.0K   0% /sys/fs/cgroup
tmpfs           3.9G  8.0K  3.9G   1% /tmp
/dev/sda1       256M   72M  185M  28% /boot
none            4.0K     0  4.0K   0% /run/lock
none            3.9G     0  3.9G   0% /sys/fs/bpf
tmpfs           785M     0  785M   0% /run/user/1000
```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem      Size  Used Avail Use% Mounted on
udev            3.9G     0  3.9G   0% /dev
tmpfs           785M  1.6M  784M   1% /run
/dev/sda2        20G  4.1G   16G  21% /
none            4.0K     0  4.0K   0% /sys/fs/cgroup
tmpfs           3.9G  8.0K  3.9G   1% /tmp
/dev/sda1       256M   72M  185M  28% /boot
none            4.0K     0  4.0K   0% /run/lock
none            3.9G     0  3.9G   0% /sys/fs/bpf
tmpfs           785M     0  785M   0% /run/user/1000
```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem      Size  Used Avail Use% Mounted on
udev            3.9G     0  3.9G   0% /dev
tmpfs           785M  1.6M  784M   1% /run
/dev/sda2        20G  4.1G   16G  21% /
none            4.0K     0  4.0K   0% /sys/fs/cgroup
tmpfs           3.9G  8.0K  3.9G   1% /tmp
/dev/sda1       256M   72M  185M  28% /boot
none            4.0K     0  4.0K   0% /run/lock
none            3.9G     0  3.9G   0% /sys/fs/bpf
tmpfs           785M     0  785M   0% /run/user/1000
```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem      Size  Used Avail Use% Mounted on
udev            3.9G     0  3.9G   0% /dev
tmpfs           785M  1.6M  784M   1% /run
/dev/sda2        20G  4.1G   16G  21% /
none            4.0K     0  4.0K   0% /sys/fs/cgroup
tmpfs           3.9G  8.0K  3.9G   1% /tmp
/dev/sda1       256M   72M  185M  28% /boot
none            4.0K     0  4.0K   0% /run/lock
none            3.9G     0  3.9G   0% /sys/fs/bpf
tmpfs           785M     0  785M   0% /run/user/1000
```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Filesystem      Size  Used Avail Use% Mounted on
udev            3.9G     0  3.9G   0% /dev
tmpfs           785M  1.6M  784M   1% /run
/dev/sda2        20G  4.1G   16G  21% /
none            4.0K     0  4.0K   0% /sys/fs/cgroup
tmpfs           3.9G  8.0K  3.9G   1% /tmp
/dev/sda1       256M   72M  185M  28% /boot
none            4.0K     0  4.0K   0% /run/lock
none            3.9G     0  3.9G   0% /sys/fs/bpf
tmpfs           785M     0  785M   0% /run/user/1000
```


## Q16 lscpu
- ATT&CK：T1082 System Information Discovery
- 考點：Architecture / CPU(s) / Model name / 欄位齊全
- 通過：0/10

### 第 1 次 ❌ SALNLC
判定：缺少真機結構特徵：['Model name']

```
Architecture:	x86_64
CPU op-mode(s):	32-bit, 64-bit
Byte Order:	Little Endian
CPU(s):	4
On-line CPU(s) list:	0-3
Thread(s) per core:	1
Core(s) per socket:	4
Socket(s):	1
NUMA node(s):	1
Vendor ID:	GenuineIntel
CPU family:	6
Model:	62
Stepping:	4
CPU MHz:	2399.985
BogoMIPS:	4799.97
Hypervisor vendor:	KVM
Virtualization type:	kvm
L1d cache:	32K
L1i cache:	32K
L2 cache:	256K
L3 cache:	20480K
NUMA node0 CPU(s):	0-3
```

### 第 2 次 ❌ SALNLC
判定：缺少真機結構特徵：['Model name']

```
Architecture:	x86_64
CPU op-mode(s):	32-bit, 64-bit
Byte Order:	Little Endian
CPU(s):	4
On-line CPU(s) list:	0-3
Thread(s) per core:	1
Core(s) per socket:	4
Socket(s):	1
NUMA node(s):	1
Vendor ID:	GenuineIntel
CPU family:	6
Model:	62
Stepping:	4
CPU MHz:	2399.985
BogoMIPS:	4799.97
Hypervisor vendor:	KVM
Virtualization type:	kvm
L1d cache:	32K
L1i cache:	32K
L2 cache:	256K
L3 cache:	20480K
NUMA node0 CPU(s):	0-3
```

### 第 3 次 ❌ SALNLC
判定：缺少真機結構特徵：['Model name']

```
Architecture:	x86_64
CPU op-mode(s):	32-bit, 64-bit
Byte Order:	Little Endian
CPU(s):	4
On-line CPU(s) list:	0-3
Thread(s) per core:	1
Core(s) per socket:	4
Socket(s):	1
NUMA node(s):	1
Vendor ID:	GenuineIntel
CPU family:	6
Model:	62
Stepping:	4
CPU MHz:	2399.985
BogoMIPS:	4799.97
Hypervisor vendor:	KVM
Virtualization type:	kvm
L1d cache:	32K
L1i cache:	32K
L2 cache:	256K
L3 cache:	20480K
NUMA node0 CPU(s):	0-3
```

### 第 4 次 ❌ SALNLC
判定：缺少真機結構特徵：['Model name']

```
Architecture:	x86_64
CPU op-mode(s):	32-bit, 64-bit
Byte Order:	Little Endian
CPU(s):	4
On-line CPU(s) list:	0-3
Thread(s) per core:	1
Core(s) per socket:	4
Socket(s):	1
NUMA node(s):	1
Vendor ID:	GenuineIntel
CPU family:	6
Model:	62
Stepping:	4
CPU MHz:	2399.985
BogoMIPS:	4799.97
Hypervisor vendor:	KVM
Virtualization type:	kvm
L1d cache:	32K
L1i cache:	32K
L2 cache:	256K
L3 cache:	20480K
NUMA node0 CPU(s):	0-3
```

### 第 5 次 ❌ SALNLC
判定：缺少真機結構特徵：['Model name']

```
Architecture:	x86_64
CPU op-mode(s):	32-bit, 64-bit
Byte Order:	Little Endian
CPU(s):	4
On-line CPU(s) list:	0-3
Thread(s) per core:	1
Core(s) per socket:	4
Socket(s):	1
NUMA node(s):	1
Vendor ID:	GenuineIntel
CPU family:	6
Model:	62
Stepping:	4
CPU MHz:	2399.985
BogoMIPS:	4799.97
Hypervisor vendor:	KVM
Virtualization type:	kvm
L1d cache:	32K
L1i cache:	32K
L2 cache:	256K
L3 cache:	20480K
NUMA node0 CPU(s):	0-3
```

### 第 6 次 ❌ SALNLC
判定：缺少真機結構特徵：['Model name']

```
Architecture:	x86_64
CPU op-mode(s):	32-bit, 64-bit
Byte Order:	Little Endian
CPU(s):	4
On-line CPU(s) list:	0-3
Thread(s) per core:	1
Core(s) per socket:	4
Socket(s):	1
NUMA node(s):	1
Vendor ID:	GenuineIntel
CPU family:	6
Model:	62
Stepping:	4
CPU MHz:	2399.985
BogoMIPS:	4799.97
Hypervisor vendor:	KVM
Virtualization type:	kvm
L1d cache:	32K
L1i cache:	32K
L2 cache:	256K
L3 cache:	20480K
NUMA node0 CPU(s):	0-3
```

### 第 7 次 ❌ SALNLC
判定：缺少真機結構特徵：['Model name']

```
Architecture:	x86_64
CPU op-mode(s):	32-bit, 64-bit
Byte Order:	Little Endian
CPU(s):	4
On-line CPU(s) list:	0-3
Thread(s) per core:	1
Core(s) per socket:	4
Socket(s):	1
NUMA node(s):	1
Vendor ID:	GenuineIntel
CPU family:	6
Model:	62
Stepping:	4
CPU MHz:	2399.985
BogoMIPS:	4799.97
Hypervisor vendor:	KVM
Virtualization type:	kvm
L1d cache:	32K
L1i cache:	32K
L2 cache:	256K
L3 cache:	20480K
NUMA node0 CPU(s):	0-3
```

### 第 8 次 ❌ SALNLC
判定：缺少真機結構特徵：['Model name']

```
Architecture:	x86_64
CPU op-mode(s):	32-bit, 64-bit
Byte Order:	Little Endian
CPU(s):	4
On-line CPU(s) list:	0-3
Thread(s) per core:	1
Core(s) per socket:	4
Socket(s):	1
NUMA node(s):	1
Vendor ID:	GenuineIntel
CPU family:	6
Model:	62
Stepping:	4
CPU MHz:	2399.985
BogoMIPS:	4799.97
Hypervisor vendor:	KVM
Virtualization type:	kvm
L1d cache:	32K
L1i cache:	32K
L2 cache:	256K
L3 cache:	20480K
NUMA node0 CPU(s):	0-3
```

### 第 9 次 ❌ SALNLC
判定：缺少真機結構特徵：['Model name']

```
Architecture:	x86_64
CPU op-mode(s):	32-bit, 64-bit
Byte Order:	Little Endian
CPU(s):	4
On-line CPU(s) list:	0-3
Thread(s) per core:	1
Core(s) per socket:	4
Socket(s):	1
NUMA node(s):	1
Vendor ID:	GenuineIntel
CPU family:	6
Model:	62
Stepping:	4
CPU MHz:	2399.985
BogoMIPS:	4799.97
Hypervisor vendor:	KVM
Virtualization type:	kvm
L1d cache:	32K
L1i cache:	32K
L2 cache:	256K
L3 cache:	20480K
NUMA node0 CPU(s):	0-3
```

### 第 10 次 ❌ SALNLC
判定：缺少真機結構特徵：['Model name']

```
Architecture:	x86_64
CPU op-mode(s):	32-bit, 64-bit
Byte Order:	Little Endian
CPU(s):	4
On-line CPU(s) list:	0-3
Thread(s) per core:	1
Core(s) per socket:	4
Socket(s):	1
NUMA node(s):	1
Vendor ID:	GenuineIntel
CPU family:	6
Model:	62
Stepping:	4
CPU MHz:	2399.985
BogoMIPS:	4799.97
Hypervisor vendor:	KVM
Virtualization type:	kvm
L1d cache:	32K
L1i cache:	32K
L2 cache:	256K
L3 cache:	20480K
NUMA node0 CPU(s):	0-3
```


## Q17 env
- ATT&CK：T1082 System Information Discovery
- 考點：環境變數 KEY=VALUE 逐行；必有 PATH、HOME
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOSTNAME=happydog
TERM=xterm
SHELL=/bin/bash
SHLVL=1
HOME=/root
LOGNAME=root
USER=root
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAIL=/var/mail/root
PWD=/root
```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOSTNAME=happydog
TERM=xterm
SHELL=/bin/bash
SHLVL=1
HOME=/root
LOGNAME=root
USER=root
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAIL=/var/mail/root
PWD=/root
```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOSTNAME=happydog
TERM=xterm
SHELL=/bin/bash
SHLVL=1
HOME=/root
LOGNAME=root
USER=root
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAIL=/var/mail/root
PWD=/root
```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOSTNAME=happydog
TERM=xterm
SHELL=/bin/bash
SHLVL=1
HOME=/root
LOGNAME=root
USER=root
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAIL=/var/mail/root
PWD=/root
```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOSTNAME=happydog
TERM=xterm
SHELL=/bin/bash
SHLVL=1
HOME=/root
LOGNAME=root
USER=root
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAIL=/var/mail/root
PWD=/root
```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOSTNAME=happydog
TERM=xterm
SHELL=/bin/bash
SHLVL=1
HOME=/root
LOGNAME=root
USER=root
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAIL=/var/mail/root
PWD=/root
```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOSTNAME=happydog
TERM=xterm
SHELL=/bin/bash
SHLVL=1
HOME=/root
LOGNAME=root
USER=root
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAIL=/var/mail/root
PWD=/root
```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOSTNAME=happydog
TERM=xterm
SHELL=/bin/bash
SHLVL=1
HOME=/root
LOGNAME=root
USER=root
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAIL=/var/mail/root
PWD=/root
```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOSTNAME=happydog
TERM=xterm
SHELL=/bin/bash
SHLVL=1
HOME=/root
LOGNAME=root
USER=root
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAIL=/var/mail/root
PWD=/root
```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
HOSTNAME=happydog
TERM=xterm
SHELL=/bin/bash
SHLVL=1
HOME=/root
LOGNAME=root
USER=root
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
MAIL=/var/mail/root
PWD=/root
```


## Q18 netstat -tlnp
- ATT&CK：T1049 System Network Connections Discovery
- 考點：表頭 Proto Recv-Q Send-Q Local Address；監聽埠格式
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      1234/postgres
tcp6       0      0 :::22                   :::*                    LISTEN      1235/sshd

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      1234/postgres
tcp6       0      0 :::22                   :::*                    LISTEN      1235/sshd

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      1234/postgres
tcp6       0      0 :::22                   :::*                    LISTEN      1235/sshd

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      1234/postgres
tcp6       0      0 :::22                   :::*                    LISTEN      1235/sshd

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      1234/postgres
tcp6       0      0 :::22                   :::*                    LISTEN      1235/sshd

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      1234/postgres
tcp6       0      0 :::22                   :::*                    LISTEN      1235/sshd

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      1234/postgres
tcp6       0      0 :::22                   :::*                    LISTEN      1235/sshd

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      1234/postgres
tcp6       0      0 :::22                   :::*                    LISTEN      1235/sshd

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      1234/postgres
tcp6       0      0 :::22                   :::*                    LISTEN      1235/sshd

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:5432          0.0.0.0:*               LISTEN      1234/postgres
tcp6       0      0 :::22                   :::*                    LISTEN      1235/sshd

```


## Q19 crontab -l
- ATT&CK：T1053 Scheduled Task/Job
- 考點：列出 cron 條目（SALC），或空/無 crontab 訊息（FALC）
- 通過：10/10

### 第 1 次 ✅ SALC
判定：有非空輸出

```
# For details see man 5 crontab
# Unlike any other cron implementation, there is no
default limit on the number of jobs you can have in a
crontab. If you are not root then you may only edit your
own crontab, not the 'inetd' crontabs used by system
administrators.
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed
30 12 * * * /root/scripts/daily_backup.sh
```

### 第 2 次 ✅ SALC
判定：有非空輸出

```
# For details see man 5 crontab
# Unlike any other cron implementation, there is no
default limit on the number of jobs you can have in a
crontab. If you are not root then you may only edit your
own crontab, not the 'inetd' crontabs used by system
administrators.
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed
30 12 * * * /root/scripts/daily_backup.sh
```

### 第 3 次 ✅ SALC
判定：有非空輸出

```
# For details see man 5 crontab
# Unlike any other cron implementation, there is no
default limit on the number of jobs you can have in a
crontab. If you are not root then you may only edit your
own crontab, not the 'inetd' crontabs used by system
administrators.
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed
30 12 * * * /root/scripts/daily_backup.sh
```

### 第 4 次 ✅ SALC
判定：有非空輸出

```
# For details see man 5 crontab
# Unlike any other cron implementation, there is no
default limit on the number of jobs you can have in a
crontab. If you are not root then you may only edit your
own crontab, not the 'inetd' crontabs used by system
administrators.
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed
30 12 * * * /root/scripts/daily_backup.sh
```

### 第 5 次 ✅ SALC
判定：有非空輸出

```
# For details see man 5 crontab
# Unlike any other cron implementation, there is no
default limit on the number of jobs you can have in a
crontab. If you are not root then you may only edit your
own crontab, not the 'inetd' crontabs used by system
administrators.
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed
30 12 * * * /root/scripts/daily_backup.sh
```

### 第 6 次 ✅ SALC
判定：有非空輸出

```
# For details see man 5 crontab
# Unlike any other cron implementation, there is no
default limit on the number of jobs you can have in a
crontab. If you are not root then you may only edit your
own crontab, not the 'inetd' crontabs used by system
administrators.
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed
30 12 * * * /root/scripts/daily_backup.sh
```

### 第 7 次 ✅ SALC
判定：有非空輸出

```
# For details see man 5 crontab
# Unlike any other cron implementation, there is no
default limit on the number of jobs you can have in a
crontab. If you are not root then you may only edit your
own crontab, not the 'inetd' crontabs used by system
administrators.
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed
30 12 * * * /root/scripts/daily_backup.sh
```

### 第 8 次 ✅ SALC
判定：有非空輸出

```
# For details see man 5 crontab
# Unlike any other cron implementation, there is no
default limit on the number of jobs you can have in a
crontab. If you are not root then you may only edit your
own crontab, not the 'inetd' crontabs used by system
administrators.
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed
30 12 * * * /root/scripts/daily_backup.sh
```

### 第 9 次 ✅ SALC
判定：有非空輸出

```
# For details see man 5 crontab
# Unlike any other cron implementation, there is no
default limit on the number of jobs you can have in a
crontab. If you are not root then you may only edit your
own crontab, not the 'inetd' crontabs used by system
administrators.
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed
30 12 * * * /root/scripts/daily_backup.sh
```

### 第 10 次 ✅ SALC
判定：有非空輸出

```
# For details see man 5 crontab
# Unlike any other cron implementation, there is no
default limit on the number of jobs you can have in a
crontab. If you are not root then you may only edit your
own crontab, not the 'inetd' crontabs used by system
administrators.
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * user-name  command to be executed
30 12 * * * /root/scripts/daily_backup.sh
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
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
PRETTY_NAME="Debian GNU/Linux 11 (bullseye)"
NAME="Debian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
```


## Q21 ls -la /root
- ATT&CK：T1083 File and Directory Discovery
- 考點：ls -l 格式：權限/連結數/擁有者/群組/大小/日期/名；必有 . 與 .. 目錄項
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 16
drwx------  4 root root 4096 Jul 14 03:20 .
drwxr-xr-x 15 root root 4096 Jul 14 03:20 ..
-rw-------  1 root root    0 Jul 14 03:20 .bash_history
-rw-r--r--  1 root root  229 Mar 15  2021 .bashrc
-rw-r--r--  1 root root  807 Mar 15  2021 profile
```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 16
drwx------  4 root root 4096 Jul 14 03:20 .
drwxr-xr-x 15 root root 4096 Jul 14 03:20 ..
-rw-------  1 root root    0 Jul 14 03:20 .bash_history
-rw-r--r--  1 root root  229 Mar 15  2021 .bashrc
-rw-r--r--  1 root root  807 Mar 15  2021 profile
```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 16
drwx------  4 root root 4096 Jul 14 03:20 .
drwxr-xr-x 15 root root 4096 Jul 14 03:20 ..
-rw-------  1 root root    0 Jul 14 03:20 .bash_history
-rw-r--r--  1 root root  229 Mar 15  2021 .bashrc
-rw-r--r--  1 root root  807 Mar 15  2021 profile
```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 16
drwx------  4 root root 4096 Jul 14 03:20 .
drwxr-xr-x 15 root root 4096 Jul 14 03:20 ..
-rw-------  1 root root    0 Jul 14 03:20 .bash_history
-rw-r--r--  1 root root  229 Mar 15  2021 .bashrc
-rw-r--r--  1 root root  807 Mar 15  2021 profile
```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 16
drwx------  4 root root 4096 Jul 14 03:20 .
drwxr-xr-x 15 root root 4096 Jul 14 03:20 ..
-rw-------  1 root root    0 Jul 14 03:20 .bash_history
-rw-r--r--  1 root root  229 Mar 15  2021 .bashrc
-rw-r--r--  1 root root  807 Mar 15  2021 profile
```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 16
drwx------  4 root root 4096 Jul 14 03:20 .
drwxr-xr-x 15 root root 4096 Jul 14 03:20 ..
-rw-------  1 root root    0 Jul 14 03:20 .bash_history
-rw-r--r--  1 root root  229 Mar 15  2021 .bashrc
-rw-r--r--  1 root root  807 Mar 15  2021 profile
```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 16
drwx------  4 root root 4096 Jul 14 03:20 .
drwxr-xr-x 15 root root 4096 Jul 14 03:20 ..
-rw-------  1 root root    0 Jul 14 03:20 .bash_history
-rw-r--r--  1 root root  229 Mar 15  2021 .bashrc
-rw-r--r--  1 root root  807 Mar 15  2021 profile
```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 16
drwx------  4 root root 4096 Jul 14 03:20 .
drwxr-xr-x 15 root root 4096 Jul 14 03:20 ..
-rw-------  1 root root    0 Jul 14 03:20 .bash_history
-rw-r--r--  1 root root  229 Mar 15  2021 .bashrc
-rw-r--r--  1 root root  807 Mar 15  2021 profile
```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 16
drwx------  4 root root 4096 Jul 14 03:20 .
drwxr-xr-x 15 root root 4096 Jul 14 03:20 ..
-rw-------  1 root root    0 Jul 14 03:20 .bash_history
-rw-r--r--  1 root root  229 Mar 15  2021 .bashrc
-rw-r--r--  1 root root  807 Mar 15  2021 profile
```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
total 16
drwx------  4 root root 4096 Jul 14 03:20 .
drwxr-xr-x 15 root root 4096 Jul 14 03:20 ..
-rw-------  1 root root    0 Jul 14 03:20 .bash_history
-rw-r--r--  1 root root  229 Mar 15  2021 .bashrc
-rw-r--r--  1 root root  807 Mar 15  2021 profile
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
MemTotal:       8384200 kB
MemFree:        1976244 kB
MemAvailable:   5991120 kB
Buffers:          26412 kB
Cached:         1697564 kB
```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:       8384200 kB
MemFree:        1976244 kB
MemAvailable:   5991120 kB
Buffers:          26412 kB
Cached:         1697564 kB
```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:       8384200 kB
MemFree:        1976244 kB
MemAvailable:   5991120 kB
Buffers:          26412 kB
Cached:         1697564 kB
```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:       8384200 kB
MemFree:        1976244 kB
MemAvailable:   5991120 kB
Buffers:          26412 kB
Cached:         1697564 kB
```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:       8384200 kB
MemFree:        1976244 kB
MemAvailable:   5991120 kB
Buffers:          26412 kB
Cached:         1697564 kB
```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:       8384200 kB
MemFree:        1976244 kB
MemAvailable:   5991120 kB
Buffers:          26412 kB
Cached:         1697564 kB
```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:       8384200 kB
MemFree:        1976244 kB
MemAvailable:   5991120 kB
Buffers:          26412 kB
Cached:         1697564 kB
```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:       8384200 kB
MemFree:        1976244 kB
MemAvailable:   5991120 kB
Buffers:          26412 kB
Cached:         1697564 kB
```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:       8384200 kB
MemFree:        1976244 kB
MemAvailable:   5991120 kB
Buffers:          26412 kB
Cached:         1697564 kB
```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
MemTotal:       8384200 kB
MemFree:        1976244 kB
MemAvailable:   5991120 kB
Buffers:          26412 kB
Cached:         1697564 kB
```


## Q24 ls -la /tmp; touch /tmp/probe_marker; ls -la /tmp
- ATT&CK：T1070 Indicator Removal / 狀態一致性
- 考點：touch 後第二次 ls 應出現 probe_marker（考跨命令 FS 狀態）
- 通過：10/10

### 第 1 次 ✅ SALC
判定：有非空輸出

```
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
```

### 第 2 次 ✅ SALC
判定：有非空輸出

```
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
```

### 第 3 次 ✅ SALC
判定：有非空輸出

```
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
```

### 第 4 次 ✅ SALC
判定：有非空輸出

```
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
```

### 第 5 次 ✅ SALC
判定：有非空輸出

```
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
```

### 第 6 次 ✅ SALC
判定：有非空輸出

```
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
```

### 第 7 次 ✅ SALC
判定：有非空輸出

```
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
```

### 第 8 次 ✅ SALC
判定：有非空輸出

```
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
```

### 第 9 次 ✅ SALC
判定：有非空輸出

```
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
```

### 第 10 次 ✅ SALC
判定：有非空輸出

```
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
total 24
drwxrwxrwt  3 root root 4096 Jul 14 03:19 .
drwxr-xr-x 22 root root 4096 Jul 14 03:19 ..
drwx------ 2 user user 4096 Jul 14 03:19 x
-rw-r--r-- 1 root root    0 Jul 21 06:35 testfile
```


## Q25 hostname
- ATT&CK：T1082 System Information Discovery
- 考點：單行主機名；須與 uname -a（Q1）宣稱的主機名一致
- 通過：10/10

### 第 1 次 ✅ SALC
判定：有非空輸出

```
happydog
```

### 第 2 次 ✅ SALC
判定：有非空輸出

```
happydog
```

### 第 3 次 ✅ SALC
判定：有非空輸出

```
happydog
```

### 第 4 次 ✅ SALC
判定：有非空輸出

```
happydog
```

### 第 5 次 ✅ SALC
判定：有非空輸出

```
happydog
```

### 第 6 次 ✅ SALC
判定：有非空輸出

```
happydog
```

### 第 7 次 ✅ SALC
判定：有非空輸出

```
happydog
```

### 第 8 次 ✅ SALC
判定：有非空輸出

```
happydog
```

### 第 9 次 ✅ SALC
判定：有非空輸出

```
happydog
```

### 第 10 次 ✅ SALC
判定：有非空輸出

```
happydog
```


## Q26 cat /etc/shadow
- ATT&CK：T1003 OS Credential Dumping
- 考點：root 應可讀；格式 user:$hash:... ；或真機式權限錯誤
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890
user:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890
user:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890
user:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890
user:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890
user:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890
user:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890
user:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890
user:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890
user:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
root:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890
user:$6$rounds=100000$/saltysalt$5l4d9tH32eWxvzrRjKJLpPqQnMmOoPpQqRrSsTtUuVvWwXxYyZzAaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz1234567890

```


## Q27 w
- ATT&CK：T1033 System Owner/User Discovery
- 考點：表頭 USER TTY FROM LOGIN@ IDLE；登入時間須與模擬時鐘一致
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:35:53 up 7 days,  2:16,  1 user,  load average: 0.00, 0.01, 0.05
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    192.0.2.1        14:35    0.00s  0.06s  0.01s w
```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:35:53 up 7 days,  2:16,  1 user,  load average: 0.00, 0.01, 0.05
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    192.0.2.1        14:35    0.00s  0.06s  0.01s w
```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:35:53 up 7 days,  2:16,  1 user,  load average: 0.00, 0.01, 0.05
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    192.0.2.1        14:35    0.00s  0.06s  0.01s w
```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:35:53 up 7 days,  2:16,  1 user,  load average: 0.00, 0.01, 0.05
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    192.0.2.1        14:35    0.00s  0.06s  0.01s w
```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:35:53 up 7 days,  2:16,  1 user,  load average: 0.00, 0.01, 0.05
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    192.0.2.1        14:35    0.00s  0.06s  0.01s w
```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:35:53 up 7 days,  2:16,  1 user,  load average: 0.00, 0.01, 0.05
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    192.0.2.1        14:35    0.00s  0.06s  0.01s w
```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:35:53 up 7 days,  2:16,  1 user,  load average: 0.00, 0.01, 0.05
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    192.0.2.1        14:35    0.00s  0.06s  0.01s w
```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:35:53 up 7 days,  2:16,  1 user,  load average: 0.00, 0.01, 0.05
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    192.0.2.1        14:35    0.00s  0.06s  0.01s w
```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:35:53 up 7 days,  2:16,  1 user,  load average: 0.00, 0.01, 0.05
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    192.0.2.1        14:35    0.00s  0.06s  0.01s w
```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
 14:35:53 up 7 days,  2:16,  1 user,  load average: 0.00, 0.01, 0.05
USER     TTY      FROM             LOGIN@   IDLE   JCPU   PCPU WHAT
root     pts/0    192.0.2.1        14:35    0.00s  0.06s  0.01s w
```


## Q28 last | head -5
- ATT&CK：T1033 System Owner/User Discovery
- 考點：登入歷史：user tty host 時間範圍；時間須合理且遞減
- 通過：10/10

### 第 1 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:29:48 2026
user   pts/0        1.2.3.4    Sat Jul 22 07:15 - 07:16  (00:01)
root   pts/1        1.2.3.4    Fri Jul 21 18:30 - 19:30  (01:00)
user   pts/0        1.2.3.4    Thu Jul 20 15:45 - 16:45  (01:00)
```

### 第 2 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:29:48 2026
user   pts/0        1.2.3.4    Sat Jul 22 07:15 - 07:16  (00:01)
root   pts/1        1.2.3.4    Fri Jul 21 18:30 - 19:30  (01:00)
user   pts/0        1.2.3.4    Thu Jul 20 15:45 - 16:45  (01:00)
```

### 第 3 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:29:48 2026
user   pts/0        1.2.3.4    Sat Jul 22 07:15 - 07:16  (00:01)
root   pts/1        1.2.3.4    Fri Jul 21 18:30 - 19:30  (01:00)
user   pts/0        1.2.3.4    Thu Jul 20 15:45 - 16:45  (01:00)
```

### 第 4 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:29:48 2026
user   pts/0        1.2.3.4    Sat Jul 22 07:15 - 07:16  (00:01)
root   pts/1        1.2.3.4    Fri Jul 21 18:30 - 19:30  (01:00)
user   pts/0        1.2.3.4    Thu Jul 20 15:45 - 16:45  (01:00)
```

### 第 5 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:29:48 2026
user   pts/0        1.2.3.4    Sat Jul 22 07:15 - 07:16  (00:01)
root   pts/1        1.2.3.4    Fri Jul 21 18:30 - 19:30  (01:00)
user   pts/0        1.2.3.4    Thu Jul 20 15:45 - 16:45  (01:00)
```

### 第 6 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:29:48 2026
user   pts/0        1.2.3.4    Sat Jul 22 07:15 - 07:16  (00:01)
root   pts/1        1.2.3.4    Fri Jul 21 18:30 - 19:30  (01:00)
user   pts/0        1.2.3.4    Thu Jul 20 15:45 - 16:45  (01:00)
```

### 第 7 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:29:48 2026
user   pts/0        1.2.3.4    Sat Jul 22 07:15 - 07:16  (00:01)
root   pts/1        1.2.3.4    Fri Jul 21 18:30 - 19:30  (01:00)
user   pts/0        1.2.3.4    Thu Jul 20 15:45 - 16:45  (01:00)
```

### 第 8 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:29:48 2026
user   pts/0        1.2.3.4    Sat Jul 22 07:15 - 07:16  (00:01)
root   pts/1        1.2.3.4    Fri Jul 21 18:30 - 19:30  (01:00)
user   pts/0        1.2.3.4    Thu Jul 20 15:45 - 16:45  (01:00)
```

### 第 9 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:29:48 2026
user   pts/0        1.2.3.4    Sat Jul 22 07:15 - 07:16  (00:01)
root   pts/1        1.2.3.4    Fri Jul 21 18:30 - 19:30  (01:00)
user   pts/0        1.2.3.4    Thu Jul 20 15:45 - 16:45  (01:00)
```

### 第 10 次 ✅ SALC
判定：有非空輸出

```
wtmp begins Sun Jul 16 03:29:48 2026
user   pts/0        1.2.3.4    Sat Jul 22 07:15 - 07:16  (00:01)
root   pts/1        1.2.3.4    Fri Jul 21 18:30 - 19:30  (01:00)
user   pts/0        1.2.3.4    Thu Jul 20 15:45 - 16:45  (01:00)
```


## Q29 cat /proc/version
- ATT&CK：T1082 System Information Discovery
- 考點：核心版本字串；須與 uname -a（Q1）的 kernel 版本完全一致
- 通過：10/10

### 第 1 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-build@debian) (gcc (Debian 10.2.1-6) 10.2.1, GNU ld (GNU Binutils for Debian) 2.35.2) #1 SMP Debian 5.10.178-1 (2023-04-09)

```

### 第 2 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-build@debian) (gcc (Debian 10.2.1-6) 10.2.1, GNU ld (GNU Binutils for Debian) 2.35.2) #1 SMP Debian 5.10.178-1 (2023-04-09)

```

### 第 3 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-build@debian) (gcc (Debian 10.2.1-6) 10.2.1, GNU ld (GNU Binutils for Debian) 2.35.2) #1 SMP Debian 5.10.178-1 (2023-04-09)

```

### 第 4 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-build@debian) (gcc (Debian 10.2.1-6) 10.2.1, GNU ld (GNU Binutils for Debian) 2.35.2) #1 SMP Debian 5.10.178-1 (2023-04-09)

```

### 第 5 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-build@debian) (gcc (Debian 10.2.1-6) 10.2.1, GNU ld (GNU Binutils for Debian) 2.35.2) #1 SMP Debian 5.10.178-1 (2023-04-09)

```

### 第 6 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-build@debian) (gcc (Debian 10.2.1-6) 10.2.1, GNU ld (GNU Binutils for Debian) 2.35.2) #1 SMP Debian 5.10.178-1 (2023-04-09)

```

### 第 7 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-build@debian) (gcc (Debian 10.2.1-6) 10.2.1, GNU ld (GNU Binutils for Debian) 2.35.2) #1 SMP Debian 5.10.178-1 (2023-04-09)

```

### 第 8 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-build@debian) (gcc (Debian 10.2.1-6) 10.2.1, GNU ld (GNU Binutils for Debian) 2.35.2) #1 SMP Debian 5.10.178-1 (2023-04-09)

```

### 第 9 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-build@debian) (gcc (Debian 10.2.1-6) 10.2.1, GNU ld (GNU Binutils for Debian) 2.35.2) #1 SMP Debian 5.10.178-1 (2023-04-09)

```

### 第 10 次 ✅ SALC
判定：含全部必要結構且無缺漏

```
Linux version 5.10.0-19-amd64 (debian-build@debian) (gcc (Debian 10.2.1-6) 10.2.1, GNU ld (GNU Binutils for Debian) 2.35.2) #1 SMP Debian 5.10.178-1 (2023-04-09)

```


## Q30 sudo -l
- ATT&CK：T1069 Permission Groups Discovery
- 考點：列出 sudo 權限；root 應顯示 (ALL) ALL 或類似
- 通過：10/10

### 第 1 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on happydog:
    requiretty, env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS", env_keep+="MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE", env_keep+="LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES", env_keep+="LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE", env_keep+="LC_TIME LC_ALL LANGUAGE LINGUAS COLLATE", env_keep+="SSH_AUTH_SOCK SSH_AGENT_PID SSH_CONNECTION XAUTHORITY"

User root may run the following commands on happydog:
    (ALL : ALL) ALL
```

### 第 2 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on happydog:
    requiretty, env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS", env_keep+="MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE", env_keep+="LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES", env_keep+="LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE", env_keep+="LC_TIME LC_ALL LANGUAGE LINGUAS COLLATE", env_keep+="SSH_AUTH_SOCK SSH_AGENT_PID SSH_CONNECTION XAUTHORITY"

User root may run the following commands on happydog:
    (ALL : ALL) ALL
```

### 第 3 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on happydog:
    requiretty, env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS", env_keep+="MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE", env_keep+="LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES", env_keep+="LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE", env_keep+="LC_TIME LC_ALL LANGUAGE LINGUAS COLLATE", env_keep+="SSH_AUTH_SOCK SSH_AGENT_PID SSH_CONNECTION XAUTHORITY"

User root may run the following commands on happydog:
    (ALL : ALL) ALL
```

### 第 4 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on happydog:
    requiretty, env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS", env_keep+="MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE", env_keep+="LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES", env_keep+="LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE", env_keep+="LC_TIME LC_ALL LANGUAGE LINGUAS COLLATE", env_keep+="SSH_AUTH_SOCK SSH_AGENT_PID SSH_CONNECTION XAUTHORITY"

User root may run the following commands on happydog:
    (ALL : ALL) ALL
```

### 第 5 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on happydog:
    requiretty, env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS", env_keep+="MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE", env_keep+="LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES", env_keep+="LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE", env_keep+="LC_TIME LC_ALL LANGUAGE LINGUAS COLLATE", env_keep+="SSH_AUTH_SOCK SSH_AGENT_PID SSH_CONNECTION XAUTHORITY"

User root may run the following commands on happydog:
    (ALL : ALL) ALL
```

### 第 6 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on happydog:
    requiretty, env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS", env_keep+="MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE", env_keep+="LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES", env_keep+="LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE", env_keep+="LC_TIME LC_ALL LANGUAGE LINGUAS COLLATE", env_keep+="SSH_AUTH_SOCK SSH_AGENT_PID SSH_CONNECTION XAUTHORITY"

User root may run the following commands on happydog:
    (ALL : ALL) ALL
```

### 第 7 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on happydog:
    requiretty, env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS", env_keep+="MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE", env_keep+="LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES", env_keep+="LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE", env_keep+="LC_TIME LC_ALL LANGUAGE LINGUAS COLLATE", env_keep+="SSH_AUTH_SOCK SSH_AGENT_PID SSH_CONNECTION XAUTHORITY"

User root may run the following commands on happydog:
    (ALL : ALL) ALL
```

### 第 8 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on happydog:
    requiretty, env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS", env_keep+="MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE", env_keep+="LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES", env_keep+="LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE", env_keep+="LC_TIME LC_ALL LANGUAGE LINGUAS COLLATE", env_keep+="SSH_AUTH_SOCK SSH_AGENT_PID SSH_CONNECTION XAUTHORITY"

User root may run the following commands on happydog:
    (ALL : ALL) ALL
```

### 第 9 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on happydog:
    requiretty, env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS", env_keep+="MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE", env_keep+="LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES", env_keep+="LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE", env_keep+="LC_TIME LC_ALL LANGUAGE LINGUAS COLLATE", env_keep+="SSH_AUTH_SOCK SSH_AGENT_PID SSH_CONNECTION XAUTHORITY"

User root may run the following commands on happydog:
    (ALL : ALL) ALL
```

### 第 10 次 ✅ SALC
判定：有非空輸出

```
Matching Defaults entries for root on happydog:
    requiretty, env_reset, env_keep="COLORS DISPLAY HOSTNAME HISTSIZE KDEDIR LS_COLORS", env_keep+="MAIL PS1 PS2 QTDIR USERNAME LANG LC_ADDRESS LC_CTYPE", env_keep+="LC_COLLATE LC_IDENTIFICATION LC_MEASUREMENT LC_MESSAGES", env_keep+="LC_MONETARY LC_NAME LC_NUMERIC LC_PAPER LC_TELEPHONE", env_keep+="LC_TIME LC_ALL LANGUAGE LINGUAS COLLATE", env_keep+="SSH_AUTH_SOCK SSH_AGENT_PID SSH_CONNECTION XAUTHORITY"

User root may run the following commands on happydog:
    (ALL : ALL) ALL
```
