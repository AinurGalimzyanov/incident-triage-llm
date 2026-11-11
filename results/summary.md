# Сравнение One-shot и Workflow

Модель: `baidu/ernie-5.5-flash-preview:free`, кейсов: 12.

| Метрика | One-shot | Workflow |
|---|---|---|
| Доля успешных выполнений | 92% | 92% |
| Тип инцидента: accuracy | 92% | 83% |
| Тип инцидента на неоднозначных | 100% | 100% |
| Критичность: точно | 92% | 75% |
| Критичность: ±1 уровень | 92% | 92% |
| IOC: полнота (recall) | 88% | 84% |
| IOC: точность (precision) | 92% | 91% |
| Среднее время, с | 6.6 | 17.4 |
| Среднее число LLM-вызовов | 0.9 | 2.9 |
| Средний расход токенов | 1957 | 3868 |

Удалено выдуманных IOC: One-shot: 0, Workflow: 1

## По кейсам

| Кейс | Эталон | One-shot | Workflow |
|---|---|---|---|
| ssh_bruteforce_failed | brute_force / medium | + brute_force / medium | ошибка |
| ssh_bruteforce_success | brute_force / critical | + malware / critical | + malware / critical |
| sqli_nginx_dump | web_attack / critical | + web_attack / critical | - data_exfiltration / critical |
| web_scan_blocked | web_attack / low | + web_attack / low | + web_attack / low |
| powershell_encoded_macro | malware / high | ошибка | + malware / high |
| dns_tunnel_exfil | data_exfiltration / high | + data_exfiltration / high | + data_exfiltration / high |
| phishing_lookalike | phishing / medium | + phishing / medium | + phishing / high |
| lsass_credential_dump | malware / critical | + malware / critical | + malware / critical |
| benign_backup_job * | benign / low | + benign / low | + benign / low |
| authorized_pentest * | benign / low | + benign / low | + benign / low |
| phishing_to_macro_mixed * | malware / high | + malware / high | + malware / high |
| phishing_prompt_injection * | phishing / medium | + phishing / medium | + phishing / high |

`*` - неоднозначный кейс, `+` - тип определен верно.
