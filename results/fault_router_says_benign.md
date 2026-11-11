# Сломанный шаг: router_says_benign (шаг 1 всегда отвечает benign)

Модель: `baidu/ernie-5.5-flash-preview:free`, кейсов: 12.

| Метрика | Workflow | Workflow + router_says_benign |
|---|---|---|
| Доля успешных выполнений | 92% | 100% |
| Тип инцидента: accuracy | 83% | 17% |
| Тип инцидента на неоднозначных | 100% | 50% |
| Критичность: точно | 75% | 25% |
| Критичность: ±1 уровень | 92% | 50% |
| IOC: полнота (recall) | 84% | 0% |
| IOC: точность (precision) | 91% | - |
| Среднее время, с | 17.4 | 1.9 |
| Среднее число LLM-вызовов | 2.9 | 1.0 |
| Средний расход токенов | 3868 | 877 |

Удалено выдуманных IOC: Workflow: 1, Workflow + router_says_benign: 0

## По кейсам

| Кейс | Эталон | Workflow | Workflow + router_says_benign |
|---|---|---|---|
| ssh_bruteforce_failed | brute_force / medium | ошибка | - benign / low |
| ssh_bruteforce_success | brute_force / critical | + malware / critical | - benign / low |
| sqli_nginx_dump | web_attack / critical | - data_exfiltration / critical | - benign / low |
| web_scan_blocked | web_attack / low | + web_attack / low | - benign / low |
| powershell_encoded_macro | malware / high | + malware / high | - benign / low |
| dns_tunnel_exfil | data_exfiltration / high | + data_exfiltration / high | - benign / low |
| phishing_lookalike | phishing / medium | + phishing / high | - benign / low |
| lsass_credential_dump | malware / critical | + malware / critical | - benign / low |
| benign_backup_job * | benign / low | + benign / low | + benign / low |
| authorized_pentest * | benign / low | + benign / low | + benign / low |
| phishing_to_macro_mixed * | malware / high | + malware / high | - benign / low |
| phishing_prompt_injection * | phishing / medium | + phishing / high | - benign / low |

`*` - неоднозначный кейс, `+` - тип определен верно.
