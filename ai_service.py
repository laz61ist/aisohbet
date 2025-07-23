import os
import sys
import json
import base64
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, SystemMessage

# .env dosyasındaki environment variable'ları yükle
load_dotenv()

# API Anahtarlarını environment variable'lardan al
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# --- Yeni Modüler Yapı Başlangıcı ---

def load_experts_config(filepath="experts.json"):
    """Uzman yapılandırmasını JSON dosyasından yükler."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise Exception(f"{filepath} dosyası bulunamadı.")
    except json.JSONDecodeError:
        raise Exception(f"{filepath} dosyası geçerli bir JSON formatında değil.")

EXPERTS_CONFIG = load_experts_config()

def get_llm_instance(provider, model_name):
    """Sağlayıcıya ve model adına göre LLM örneği döndürür."""
    if provider == "openai":
        if not OPENAI_API_KEY: return None
        return ChatOpenAI(model=model_name, temperature=0.7, api_key=OPENAI_API_KEY)
    elif provider == "google":
        if not GOOGLE_API_KEY: return None
        return ChatGoogleGenerativeAI(model=model_name, temperature=0.7, google_api_key=GOOGLE_API_KEY)
    elif provider == "anthropic":
        if not ANTHROPIC_API_KEY: return None
        return ChatAnthropic(model=model_name, temperature=0.7, api_key=ANTHROPIC_API_KEY)
    return None

def get_expert_response(expert_name, user_prompt, history):
    """Belirtilen uzman modelden yanıt alır (JSON yapılandırmasına göre)."""

    if expert_name not in EXPERTS_CONFIG:
        return f"@{expert_name} adında bir uzman bulunamadı."

    expert_info = EXPERTS_CONFIG[expert_name]

    try:
        llm = get_llm_instance(expert_info["model_provider"], expert_info["model_name"])
    except Exception as e:
        return f"Hata: {expert_name.capitalize()} için model örneği oluşturulurken sorun oluştu: {str(e)}"

    if not llm:
        return f"@{expert_name.capitalize()} uzmanı için API anahtarı yapılandırılmamış veya model yüklenemedi."

    # Geçmişi LangChain formatına çevir
    langchain_history = []
    for msg in history:
        if msg['role'] == 'user':
            langchain_history.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'ai':
            try:
                ai_content = json.loads(msg['content'])
                content_to_add = ai_content.get('summary', ai_content.get('direct_response', ''))
                if content_to_add:
                    langchain_history.append(SystemMessage(content=content_to_add))
            except (json.JSONDecodeError, TypeError):
                langchain_history.append(SystemMessage(content=msg['content']))

    system_message = SystemMessage(content=expert_info["prompt"])
    human_message = HumanMessage(content=user_prompt)

    # Sistem mesajı + geçmiş + güncel mesaj
    messages = [system_message] + langchain_history + [human_message]

    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"Hata: {expert_name.capitalize()} uzmanına ulaşılırken bir sorun oluştu: {str(e)}"

def main(payload):
    """Ana iş mantığını yürüten fonksiyon."""

    user_prompt = payload.get('current_message', '')
    history = payload.get('history', [])

    # --- Yeni Modüler Yapı Bitişi ---

    lower_prompt = user_prompt.lower()

    # @-etiketlemeyi dinamik olarak kontrol et
    tagged_expert = None
    for expert_name in EXPERTS_CONFIG:
        if expert_name != "moderator" and lower_prompt.startswith(f"@{expert_name}"):
            tagged_expert = expert_name
            break

    if tagged_expert:
        prompt_text = user_prompt[len(f"@{tagged_expert}"):].strip()
        response = get_expert_response(tagged_expert, prompt_text, history)
        result = {"direct_response": response}
    else:
        # Moderatör modu
        prompt_text = user_prompt
        experts_to_run = [name for name in EXPERTS_CONFIG if name != "moderator"]
        analyses = {}
        for expert in experts_to_run:
            analyses[expert] = get_expert_response(expert, prompt_text, history)

        moderator_config = EXPERTS_CONFIG.get("moderator")
        if not moderator_config:
            return {"error": "Moderator yapılandırması 'experts.json' dosyasında bulunamadı."}

        try:
            moderator_llm = get_llm_instance(moderator_config["model_provider"], moderator_config["model_name"])
            if not moderator_llm:
                return {"error": "Özetleme yapmak için gereken Moderatör AI yapılandırılmamış veya API anahtarı eksik."}
        except Exception as e:
            return {"error": f"Moderatör modeli yüklenirken hata oluştu: {str(e)}"}


        # Dinamik olarak moderatör prompt'unu oluştur
        analysis_texts = []
        for expert, analysis in analyses.items():
            analysis_texts.append(f"{expert.capitalize()} Analizi:\n{analysis}")

        moderator_prompt_text = f"""
        Bir proje fikri hakkında çeşitli uzmanlardan aşağıdaki analizler geldi.
        Görevin, bu analizleri birleştirerek kullanıcıya bütünsel, anlaşılır ve eyleme geçirilebilir bir özet sunmaktır.
        Özetin, her bir uzmanın kilit noktalarını vurgulamalı ve olası çelişkileri veya sinerjileri belirtmelidir.

        --- UZMAN ANALİZLERİ ---
        {"\n\n".join(analysis_texts)}
        --- UZMAN ANALİZLERİ SONU ---

        Lütfen yukarıdaki analizlere dayanarak kapsamlı bir özet oluştur.
        """

        moderator_messages = [
            SystemMessage(content=moderator_config["prompt"]),
            HumanMessage(content=moderator_prompt_text)
        ]

        try:
            summary_response = moderator_llm.invoke(moderator_messages)
            summary = summary_response.content
        except Exception as e:
            summary = f"Özet oluşturulurken bir hata meydana geldi: {str(e)}"

        result = {
            "summary": summary,
            "details": analyses
        }

    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Gerekli argüman sağlanmadı."}))
        sys.exit(1)

    try:
        # Base64 ile kodlanmış payload'ı al ve çöz
        encoded_payload = sys.argv[1]
        decoded_payload = base64.b64decode(encoded_payload)
        payload = json.loads(decoded_payload)

        # Ana fonksiyonu çalıştır
        final_result = main(payload)

        # Sonucu JSON formatında standart çıktıya bas
        print(json.dumps(final_result, indent=4, ensure_ascii=False))

    except json.JSONDecodeError:
        print(json.dumps({"error": "Gelen veri formatı bozuk (JSON değil)."}))
        sys.exit(1)
    except Exception as e:
        # Genel hata yakalama
        import traceback
        error_message = f"Python scriptinde beklenmedik bir hata oluştu: {str(e)}"
        # Hatanın detayını stderr'e yazmak, PHP'nin yakalaması için iyi bir pratik olabilir
        sys.stderr.write(f"{error_message}\n{traceback.format_exc()}")
        print(json.dumps({"error": error_message}))
        sys.exit(1)
