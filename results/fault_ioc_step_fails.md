# Сломанный шаг: ioc_step_fails (шаг 2а всегда падает)

Модель: `baidu/ernie-5.5-flash-preview:free`, кейсов: 12.

| Метрика | Workflow | Workflow + ioc_step_fails |
|---|---|---|
| Доля успешных выполнений | 92% | 100% |
| Тип инцидента: accuracy | 83% | 92% |
| Тип инцидента на неоднозначных | 100% | 100% |
| Критичность: точно | 75% | 100% |
| Критичность: ±1 уровень | 92% | 100% |
| IOC: полнота (recall) | 84% | 0% |
| IOC: точность (precision) | 91% | - |
| Среднее время, с | 17.4 | 12.9 |
| Среднее число LLM-вызовов | 2.9 | 2.8 |
| Средний расход токенов | 3868 | 3375 |

Удалено выдуманных IOC: Workflow: 1, Workflow + ioc_step_fails: 0

## По кейсам

| Кейс | Эталон | Workflow | Workflow + ioc_step_fails |
|---|---|---|---|
| ssh_bruteforce_failed | brute_force / medium | ошибка | + brute_force / medium |
| ssh_bruteforce_success | brute_force / critical | + malware / critical | + malware / critical |
| sqli_nginx_dump | web_attack / critical | - data_exfiltration / critical | - data_exfiltration / critical |
| web_scan_blocked | web_attack / low | + web_attack / low | + web_attack / low |
| powershell_encoded_macro | malware / high | + malware / high | + malware / high |
| dns_tunnel_exfil | data_exfiltration / high | + data_exfiltration / high | + data_exfiltration / high |
| phishing_lookalike | phishing / medium | + phishing / high | + phishing / medium |
| lsass_credential_dump | malware / critical | + malware / critical | + malware / critical |
| benign_backup_job * | benign / low | + benign / low | + benign / low |
| authorized_pentest * | benign / low | + benign / low | + benign / low |
| phishing_to_macro_mixed * | malware / high | + malware / high | + malware / high |
| phishing_prompt_injection * | phishing / medium | + phishing / high | + phishing / medium |

`*` - неоднозначный кейс, `+` - тип определен верно.
