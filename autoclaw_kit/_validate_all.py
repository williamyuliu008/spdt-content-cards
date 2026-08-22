"""批量校验 地理 + 政治 所有新套卡"""
import os, json, sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

SUBJECTS = ['地理', '政治']
total = 0
pass_n = 0
warn_n = 0
err_n = 0
issues = []  # [(套名, errs, warns)]

import subprocess, tempfile
validate = r'D:\4_data\knowledge_cards\autoclaw_kit\07_validate.py'

for subj in SUBJECTS:
    cards_dir = f'D:\\4_data\\knowledge_cards\\{subj}\\cards'
    if not os.path.exists(cards_dir):
        continue
    sets = sorted([d for d in os.listdir(cards_dir) if os.path.isdir(os.path.join(cards_dir, d))])
    for s in sets:
        total += 1
        # 跑校验
        try:
            r = subprocess.run(['python', '-X', 'utf8', validate, cards_dir],
                             capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=30)
            out = r.stdout
            # 解析最后几行
            for line in out.split('\n'):
                if '套卡数' in line:
                    # 提取数据
                    pass
            # 简单判断：找 "错误: 0" / "套卡数: X"
            n_err = 0
            n_warn = 0
            for line in out.split('\n'):
                if '[ERR]' in line:
                    n_err += 1
                if '[WARN]' in line:
                    n_warn += 1
            if n_err == 0:
                pass_n += 1
            else:
                err_n += 1
                issues.append((f'{subj}/{s}', n_err, n_warn))
            warn_n += n_warn
        except Exception as e:
            err_n += 1
            issues.append((f'{subj}/{s}', -1, 0))

print(f'\n=== 校验汇总 ===')
print(f'总套数: {total}')
print(f'PASS: {pass_n}')
print(f'ERROR: {err_n}')
print(f'WARN: {warn_n} (软警告)')
print(f'\n有 ERR 的套（前 20）:')
for s, e, w in issues[:20]:
    print(f'  {s}: {e} ERR, {w} WARN')
