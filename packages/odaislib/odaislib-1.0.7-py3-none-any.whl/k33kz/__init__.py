# The Script And The Library For Odai - @K33Kz -- @K33Ka
# السكربت و المكتبة لعدي @K33Kz - @K33Ka
import requests,re,json,time;from uuid import uuid4

class basic:
    @staticmethod
    def login(email, password, proxies=None):
        r = requests.get("https://www.facebook.com/?_rd")
        m = re.search(r'privacy_mutation_token\s*["\']?\s*[:=]\s*["\']?([A-Za-z0-9_\-:.]+)', r.text)
        token = m.group(1) if m else None
        cok = r.cookies
        fr = cok.get('fr', '')
        cookies = {
        'datr': '1uBDaYSNCnmSWNXK148RNXci',
        'sb': '1uBDaSJj0uSvPcQFj-09YEP-',
        'ps_l': '1',
        'ps_n': '1',
        'dpr': '2.8035895824432373',
        'm_pixel_ratio': '2.549999952316284',
        'fr': fr,
        'wd': '891x815',
    }
        headers = {
        'authority': 'www.facebook.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ar-AE,ar;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        'dpr': '2.549999952316284',
        'origin': 'https://www.facebook.com',
        'referer': 'https://www.facebook.com/?_rdr',
        'sec-ch-prefers-color-scheme': 'dark',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-full-version-list': '"Chromium";v="139.0.7339.0", "Not;A=Brand";v="99.0.0.0"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Linux"',
        'sec-ch-ua-platform-version': '""',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'viewport-width': '980',
    }
        data = {
            'jazoest': '21013',
            'lsd': 'AdGmEblaQpg',
            'email': email,
            'login_source': 'comet_headerless_login',
            'next': '',
            'encpass': f'PWD_BROWSER:0:{int(time.time())}:{password}',
        }
        response = requests.post(f'https://www.facebook.com/login/?privacy_mutation_token={token}&next',cookies=cookies,headers=headers,data=data,proxies=proxies).text
        account_id = re.search(r'ACCOUNT_ID["\']?\s*[:=]\s*["\']?(\d+)', response)
        user_id = re.search(r'USER_ID["\']?\s*[:=]\s*["\']?(\d+)', response)
        username = re.search(r'USERNAME["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_.]+)', response)
        if (account_id and account_id.group(1) != "0" and 
            user_id and user_id.group(1) != "0" and 
            username and username.group(1) != "0"):
            return json.dumps({
                "status": "success",
                "account_id": account_id.group(1),
                "username": username.group(1),
                "email": email,
                "password": password,
                "by": "Odai - @K33Kz - @K33Ka"
            })
        elif ('Please complete the security check to log in.' in response or 'two_step_verification' in response or '2fa' in response or '2FA' in response):
            return json.dumps({
                "status": "checkpoint",
                "account_id": account_id.group(1),
                "username": username.group(1),
                "email": email,
                "password": password,
                "by": "Odai - @K33Kz - @K33Ka"
            })
        elif ('كلمة السر التي أدخلتها غير صحيحة.' in response or 
              'هل نسيت كلمة السر؟' in response):
            return json.dumps({
                "status": "bad_password",
                "email": email,
                "password": password,
                "by": "Odai - @K33Kz - @K33Ka"
            })
            
        elif 'البريد الإلكتروني أو رقم الهاتف المحمول الذي أدخلته غير مرتبط بحساب.' in response:
            return json.dumps({
                "status": "user_not_found",
                "email": email,
                "password": password,
                "by": "Odai - @K33Kz - @K33Ka"
            })
            
        else:
            return json.dumps({
                "status": "unknown_response",
                "email": email,
                "password": password,
                "by": "Odai - @K33Kz - @K33Ka"
            })
class auth:
    @staticmethod
    def login(email, password,proxies=None):
        data = {
            "locale": "en_GB",
            "format": "json",
            "email": email,
            "password": password,
            "access_token": "200424423651082|2a9918c6bcd75b94cefcbb5635c6ad16",
            "generate_session_cookies": 1
        }
        headers = {
            'user-agent': 'Mozilla/5.0',
            'Host': 'graph.facebook.com',
            'Content-Type': 'application/json;charset=utf-8'
        } 
        response = requests.post("https://b-graph.facebook.com/auth/login",data=data,headers=headers,proxies=proxies)
        result = response.json()
        text = response.text
        if 'access_token' in result or 'session_key' in result:
            uid = result.get('uid', '')
            cookies = ';'.join(i['name'] + '=' + i['value'] for i in result.get('session_cookies', []))
            return {
                "status": "success",
                "uid": uid,
                "cookies": cookies,
                "email": email,
                "password": password,
                "by": "Odai - @K33Kz - @K33Ka"
            }
        elif ('www.facebook.com' in result.get('error', {}).get('message', '') or 'Please complete the security check to log in.' in text or 'two_step_verification' in text):
            return {
                "status": "checkpoint",
                "email": email,
                "password": password,
                "by": "Odai - @K33Kz - @K33Ka"
            }
        else:
            return {
                "status": "bad_login",
                "email": email,
                "password": password,
                "by": "Odai - @K33Kz - @K33Ka"
            }
class mobile:
    @staticmethod
    def login(email, password, proxies=None):
        payload = {
    'method': "post",
    'pretty': "false",
    'format': "json",
    'server_timestamps': "true",
    'locale': "en_EN",
    'purpose': "fetch",
    'fb_api_req_friendly_name': "FbBloksActionRootQuery-com.bloks.www.bloks.caa.login.async.send_login_request",
    'fb_api_caller_class': "graphservice",
    'client_doc_id': "11994080425074657009809260413",
    'fb_api_client_context': json.dumps({"is_background": False}),
    'variables': json.dumps({
        "params": {
            "params": json.dumps({
                "params": json.dumps({
                    "client_input_params": {
                        "sim_phones": [],
                        "aymh_accounts": [{
                            "profiles": {
                                "id": {
                                    "is_derived": 0,
                                    "credentials": [],
                                    "account_center_id": "",
                                    "profile_picture_url": "",
                                    "small_profile_picture_url": None,
                                    "notification_count": 0,
                                    "token": "",
                                    "last_access_time": 0,
                                    "has_smartlock": 0,
                                    "credential_type": "none",
                                    "password": "",
                                    "from_accurate_privacy_result": 0,
                                    "dbln_validated": 0,
                                    "user_id": "",
                                    "name": "",
                                    "nta_eligibility_reason": None,
                                    "username": "",
                                    "account_source": ""
                                }
                            },
                            "id": ""
                        }],
                        "secure_family_device_id": str(uuid4()),
                        "attestation_result": {                            
                        },
                        "has_granted_read_contacts_permissions": 0,
                        "auth_secure_device_id": "null",
                        "has_whatsapp_installed": 1,
                        "password": f"#PWD_FB4A:0:{str(int(time.time()))}:{password}",
                        "sso_token_map_json_string": "",
                        "block_store_machine_id": None,
                        "cloud_trust_token": None,
                        "event_flow": "login_manual",
                        "password_contains_non_ascii": "false",
                        "sim_serials": [],
                        "client_known_key_hash": "",
                        "encrypted_msisdn": "",
                        "has_granted_read_phone_permissions": 0,
                        "app_manager_id": str(uuid4()),
                        "should_show_nested_nta_from_aymh": 1,
                        "device_id": str(uuid4()),
                        "zero_balance_state": "data",
                        "login_attempt_count": 1,
                        "flash_call_permission_status": {
                            "READ_PHONE_STATE": "DENIED",
                            "READ_CALL_LOG": "DENIED",
                            "ANSWER_PHONE_CALLS": "DENIED"
                        },
                        "accounts_list": [],
                        "family_device_id": str(uuid4()),
                        "fb_ig_device_id": [],
                        "device_emails": [],
                        "try_num": 3,
                        "lois_settings": {
                            "lois_token": ""
                        },
                        "event_step": "home_page",
                        "headers_infra_flow_id": str(uuid4()),
                        "openid_tokens": {},
                        "contact_point": email
                    },
                    "server_params": {
                        "should_trigger_override_login_2fa_action": 0,
                        "is_vanilla_password_page_empty_password": 0,
                        "is_from_logged_out": 0,
                        "should_trigger_override_login_success_action": 0,
                        "login_credential_type": "none",
                        "server_login_source": "login",
                        "waterfall_id": str(uuid4()),
                        "two_step_login_type": "one_step_login",
                        "login_source": "Login",
                        "is_platform_login": 0,
                        "pw_encryption_try_count": 1,
                        "INTERNAL__latency_qpl_marker_id": 36707139,
                        "is_from_aymh": 0,
                        "offline_experiment_group": None,
                        "is_from_landing_page": 0,
                        "password_text_input_id": None,
                        "is_from_empty_password": 0,
                        "is_from_msplit_fallback": 0,
                        "ar_event_source": "login_home_page",
                        "username_text_input_id": None,
                        "layered_homepage_experiment_group": None,
                        "device_id": str(uuid4()),
                        "INTERNAL__latency_qpl_instance_id": 1.06996309100672e14,
                        "reg_flow_source": "login_home_native_integration_point",
                        "is_caa_perf_enabled": 1,
                        "credential_type": "password",
                        "is_from_password_entry_page": 0,
                        "caller": "gslr",
                        "family_device_id": str(uuid4()),
                        "is_from_assistive_id": 0,
                        "access_flow_version": "pre_mt_behavior",
                        "is_from_logged_in_switcher": 0
                    }
                })
            }),
            "bloks_versioning_id": "c42a4bd8f99cb2bd57ea74ca2b690710be5a50faa60a68bb9bcc524fe6c63e7a",
            "app_id": "com.bloks.www.bloks.caa.login.async.send_login_request"
        },
        "scale": "3",
        "nt_context": {
            "using_white_navbar": True,
            "styles_id": "3b115a54b620c39392b96bdca4c5237f",
            "pixel_ratio": 3,
            "is_push_on": True,
            "debug_tooling_metadata_token": None,
            "is_flipper_enabled": False,
            "theme_params": [{
                "value": [],
                "design_system_name": "FDS"
            }],
            "bloks_version": "c42a4bd8f99cb2bd57ea74ca2b690710be5a50faa60a68bb9bcc524fe6c63e7a"
        }
    }),
    'fb_api_analytics_tags': json.dumps(["GraphServices"]),
    'client_trace_id': "a5bba4f8-b87f-4b73-8d9a-44226255a84c"
}
        headers = {
            'User-Agent': "[FBAN/FB4A;FBAV/536.0.0.46.77;FBBV/810163229;FBDM/{density=2.75,width=1080,height=2220};FBLC/en_EN;FBRV/0;FBCR/Yemen Mobile;FBMF/Xiaomi;FBBD/Redmi;FBPN/com.facebook.katana;FBDV/Redmi Note 10 Pro;FBSV/11;FBOP/1;FBCA/arm64-v8a:;]",
            'x-fb-friendly-name': "FbBloksActionRootQuery-com.bloks.www.bloks.caa.login.async.send_login_request",
            'authorization': "OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32",
}
        response = requests.post("https://graph-fallback.facebook.com/graphql",data=payload,headers=headers,proxies=proxies)
        response_text = response.text
        if re.search(r'"access_token":"(.*?)"', response_text.replace("/", "").replace("\\", "")):
            token_match = re.search(r'"access_token":"(.*?)"', response_text.replace("/", "").replace("\\", ""))
            return {
                "status": "success",
                "access_token": token_match.group(1),
                "email": email,
                "password": password,
                "by": "Odai - @K33Kz - @K33Ka"
            }
        if "Invalid username or password" in response_text or 'override_login_2fa_action' in response_text.lower():
            return {
                "status": "bad_credentials",
                "email": email,
                "password": password,
                "by": "Odai - @K33Kz - @K33Ka"
            }
        else:
            return {
            "status": "unknown_response",
            "email": email,
            "password": password,
            "by": "Odai - @K33Kz - @K33Ka"
            
        }
class apps:
    @staticmethod
    def get_linked_apps(cookies):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0",
            "Host": "m.facebook.com",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        cookie_str = f"datr={cookies.get('datr', '')}; fr={cookies.get('fr', '')}; sb=3lMpYKwYO6_QcWBti1wPKbjK; m_pixel_ratio=1; wd=1284x422; c_user={cookies.get('c_user', '')}; xs={cookies.get('xs', '')}"
        headers["Cookie"] = cookie_str
        response = requests.get("https://www.facebook.com/settings?tab=applications&ref=settings",headers=headers)
        apps_matches = re.findall(r'\",\"app_name\":\"([^\"]+)\",\"', response.text)
        linked_apps = list(set(apps_matches))
        return linked_apps

import requests, re, json, time, os, random
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

class InstaResetTool:
    @staticmethod
    class InstaClient:
        def __init__(self):
            self.session = requests.Session()
            self.csrf_token = None
            self.response_history = []
            self.session.headers.update({
                "User-Agent": "Instagram 320.0.0.34.109 Android (33/13; 420dpi; 1080x2340; samsung; SM-A546B; a54x; exynos1380; en_US; 465123678)",
                'X-IG-App-Startup-Country': 'US',
                'X-Bloks-Version-Id': 'ce555e5500576acd8e84a66018f54a05720f2dce29f0bb5a1f97f0c10d6fac48',
                'X-IG-App-ID': '567067343352427',
                'X-IG-Connection-Type': 'WIFI',
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                'accept-encoding': 'gzip, deflate',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                "Connection": "keep-alive",
                "Origin": "https://www.instagram.com",
                "Referer": "https://www.instagram.com/",
            })

        def cev1(self, text: str) -> Optional[str]:
            patterns = [
                r'"csrf_token":"(.*?)"',
                r'csrftoken=([a-zA-Z0-9]+)',
            ]
            for p in patterns:
                m = re.search(p, text)
                if m:
                    self.csrf_token = m.group(1)
                    self.session.headers["X-CSRFToken"] = self.csrf_token
                    return self.csrf_token
            return None

        def cev2(self, url: str) -> Optional[requests.Response]:
            try:
                r = self.session.get(url, timeout=10)
                self.response_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "url": url,
                    "method": "GET",
                    "status_code": r.status_code,
                    "cookies": dict(self.session.cookies),
                    "csrf_token": self.csrf_token
                })
                self.cev1(r.text)
                return r
            except Exception as e:
                self.response_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "url": url,
                    "method": "GET",
                    "error": str(e),
                    "cookies": dict(self.session.cookies)
                })
                return None

        def cev3(self, url: str, data=None, extra_headers=None):
            headers = self.session.headers.copy()
            if extra_headers:
                headers.update(extra_headers)

            try:
                r = self.session.post(url, data=data, headers=headers, timeout=10)
                
                response_data = {
                    "timestamp": datetime.now().isoformat(),
                    "url": url,
                    "method": "POST",
                    "status_code": r.status_code,
                    "cookies": dict(self.session.cookies),
                    "request_data": data,
                    "content_length": len(r.content),
                    "response_time": r.elapsed.total_seconds()
                }
                
                self.response_history.append(response_data)
                
                if r.status_code == 200 and len(r.content) > 100:
                    return True, r, response_data

                return False, r, response_data

            except Exception as e:
                self.response_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "url": url,
                    "method": "POST",
                    "error": str(e),
                    "request_data": data,
                    "cookies": dict(self.session.cookies)
                })
                return False, None, None
    
    @staticmethod
    def generate_jazoest(email_or_username: str) -> str:
        return "21885"
    
    @staticmethod
    def extract_instagram_info(response: requests.Response) -> Dict[str, Any]:
        info = {
            "raw_response": response.text if hasattr(response, 'text') else None,
            "content_length": len(response.content) if hasattr(response, 'content') else 0,
            "elapsed_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0,
            "url": response.url if hasattr(response, 'url') else None,
        }
        
        if hasattr(response, 'headers'):
            headers = dict(response.headers)
            info["headers"] = headers
            
            instagram_headers = {}
            for key, value in headers.items():
                if any(ig_key in key.lower() for ig_key in ['ig', 'instagram', 'x-ig']):
                    instagram_headers[key] = value
            info["instagram_headers"] = instagram_headers
        
        try:
            json_data = response.json()
            info["json_response"] = json_data
            
            if isinstance(json_data, dict):
                info["instagram_status"] = json_data.get("status", "unknown")
                info["instagram_message"] = json_data.get("message", json_data.get("error_message"))
                info["instagram_user_id"] = json_data.get("user_id", json_data.get("pk"))
                info["instagram_username"] = json_data.get("username")
                info["instagram_email"] = json_data.get("email")
                info["instagram_challenge_required"] = json_data.get("challenge_required", False)
                info["instagram_two_factor_required"] = json_data.get("two_factor_required", False)
                info["instagram_contact_point"] = json_data.get("contact_point")
                info["instagram_obfuscated_contact_point"] = json_data.get("obfuscated_contact_point")
                
                if "checkpoint_url" in json_data:
                    info["checkpoint_required"] = True
                    info["checkpoint_url"] = json_data.get("checkpoint_url")
                if "flow_render_type" in json_data:
                    info["flow_type"] = json_data.get("flow_render_type")
                    
        except:
            info["json_response"] = None
            info["raw_text"] = response.text[:500] + "..." if hasattr(response, 'text') and len(response.text) > 500 else response.text if hasattr(response, 'text') else None
        
        return info

    def reset_password(self, username: str) -> Dict[str, Any]:
        client = self.InstaClient()

        client.cev2("https://www.instagram.com/")
        time.sleep(random.uniform(0.1, 0.2))
        
        client.cev2("https://www.instagram.com/accounts/password/reset/")
        
        jazoest_value = self.generate_jazoest(username)
        
        payload = {
            "email_or_username": username,
            "jazoest": jazoest_value,
        }

        success, response, request_data = client.cev3(
            "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/",
            data=payload,
            extra_headers={"X-Requested-With": "XMLHttpRequest"}
        )

        result = {
            "request_info": {
                "timestamp": datetime.now().isoformat(),
                "username": username,
                "jazoest": jazoest_value,
                "payload": payload,
                "endpoint": "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/",
                "method": "POST"
            },
            
            "session_info": {
                "csrf_token": client.csrf_token,
                "cookies": dict(client.session.cookies),
                "user_agent": client.session.headers.get("User-Agent"),
                "app_id": client.session.headers.get("X-IG-App-ID"),
                "bloks_version": client.session.headers.get("X-Bloks-Version-Id"),
            },
            
            "request_history": client.response_history,
            
            "reset_response": {
                "success": success,
                "status_code": response.status_code if response else None,
                "instagram_info": self.extract_instagram_info(response) if response else None,
            },
            
            "response_analysis": {}
        }
        
        if response:
            analysis = {
                "is_successful": success,
                "is_instagram_response": response.status_code == 200 and len(response.content) > 100,
                "has_json": False,
                "instagram_status": None,
                "email_sent": False,
                "challenge_required": False,
                "user_exists": None,
                "possible_errors": []
            }
            
            try:
                json_data = response.json()
                analysis["has_json"] = True
                analysis["instagram_status"] = json_data.get("status")
                analysis["instagram_message"] = json_data.get("message")
                
                if json_data.get("status") == "ok" or json_data.get("message") in ["Email sent", "Password reset email sent"]:
                    analysis["email_sent"] = True
                
                if json_data.get("status") == "ok":
                    analysis["user_exists"] = True
                elif "user" in json_data.get("message", "").lower() or "account" in json_data.get("message", "").lower():
                    analysis["user_exists"] = False
                    analysis["possible_errors"].append("USER_NOT_FOUND")
                
                if json_data.get("challenge_required") or json_data.get("checkpoint_url"):
                    analysis["challenge_required"] = True
                    analysis["possible_errors"].append("CHALLENGE_REQUIRED")
                    
            except:
                pass
            
            if response.status_code == 200:
                analysis["possible_errors"].append("NONE")
            elif response.status_code == 400:
                analysis["possible_errors"].append("BAD_REQUEST")
            elif response.status_code == 403:
                analysis["possible_errors"].append("FORBIDDEN")
            elif response.status_code == 429:
                analysis["possible_errors"].append("RATE_LIMIT")
            elif response.status_code >= 500:
                analysis["possible_errors"].append("SERVER_ERROR")
            
            result["response_analysis"] = analysis
        
        result["summary"] = {
            "username": username,
            "request_made": True,
            "instagram_responded": response is not None,
            "final_status": "SUCCESS" if success else "FAILED" if response else "ERROR",
            "email_possibly_sent": result.get("response_analysis", {}).get("email_sent", False),
            "user_likely_exists": result.get("response_analysis", {}).get("user_exists"),
            "timestamp_completed": datetime.now().isoformat(),
            "total_time": sum(item.get("response_time", 0) for item in client.response_history if "response_time" in item)
        }
        
        return result

    def get_full_response(self, username: str) -> Dict[str, Any]:
        return self.reset_password(username)

    def analyze_response_only(self, response_text: str) -> Dict[str, Any]:
        class MockResponse:
            def __init__(self, text):
                self.text = text
                self.content = text.encode('utf-8') if text else b''
                self.headers = {}
                self.status_code = 200
                self.elapsed = type('obj', (object,), {'total_seconds': lambda: 0})()
                self.url = "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/"
        
        mock_response = MockResponse(response_text)
        return self.extract_instagram_info(mock_response)


def cev6(usernames) -> Dict[str, Any]:
    tool = InstaResetTool()
    
    if isinstance(usernames, str):
        username = usernames
    elif isinstance(usernames, list) and len(usernames) > 0:
        username = usernames[0]
    else:
        return {"status": "error", "message": "Invalid username input"}
    
    return tool.reset_password(username)


def reset_password(username: str) -> Dict[str, Any]:
    tool = InstaResetTool()
    return tool.reset_password(username)