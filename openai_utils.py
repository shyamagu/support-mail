from pydantic import BaseModel
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

azure_openai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview"
)

model_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")

class SupportCategory(BaseModel):  
    closed: int
    bug: int  # billableからbugに変更
    user_request_category: list[str]
    support_team_response_category: list[str] 

def call_openai_completion(body: str, response_format: BaseModel):
    system_prompt = """\
入力されたマイクロソフトサポートチームと顧客とのメールスレッドを確認し、以下の項目を抽出してください。

# 抽出項目
- closed: 問い合わせがクローズされているかどうか(クローズ:1, 未クローズ:0)
- bug: 最終的にAzureやM365などマイクロソフト製品の不具合に起因する障害だったかどうか(MSの不具合:1, そうでない場合:0)

- user_request_category: 問い合わせのカテゴリ(※以下から選択、複数可。可能な限り１つ)
 - specConfirmation: マイクロソフト製品の仕様確認、設定方法の問い合わせ
 - maintenanceIssue: マイクロソフト製品のメンテナンスに関する問い合わせ
 - productFailure: マイクロソフト製品の問題・不具合に関する問い合わせ
 - quotaManagement: マイクロソフトへのクォータ制限解除や上限申請、クォータに関する質問
 - billingIssue: マイクロソフト製品の課金に関する問い合わせ
 - thirdPartyProductIssue: マイクロソフト製品ではない、他社製品(例:トレンドマイクロ、APPLE、AWS、Google、Linux、Oracle)に問題、仕様確認のための問い合わせ
 - other: その他の問い合わせ

- support_team_response_category: サポートチームの対応(※以下から選択、複数可。可能な限り１つ)
 - providedPublicDocs: パブリックドキュメントの提供
 - explainedWithoutPublicDocs: 公開情報にはない説明を提供
 - analyzedLogs: ログの解析を行い、回答を提供
 - reportedProductFailure: マイクロソフト側の製品に不具合があり、それを報告した
 - supportedByOverseasTeam: マイクロソフト本社・開発チームの支援を受けて回答をした
 - quotaManagement: クォータ制限解除や上限申請、クォータに関する回答
 - billingIssue: 課金に関する回答
 - other: その他の回答
"""

    user_prompt = body

    messages =  [  
        {'role':'system', 'content':system_prompt},  
        {'role':'user', 'content':user_prompt}  
    ]  
    event, input_token, output_token=  get_parsed_completion(messages, SupportCategory)

    return event

def get_parsed_completion(messages: list[dict], response_format: BaseModel):
    """
    Get parsed completion from Azure OpenAI.

    Args:
        messages (list[dict]): List of message dictionaries.
        response_format (BaseModel): The response format model.

    Returns:
        tuple: Parsed event, input token count, output token count.
    """
    completion = azure_openai_client.beta.chat.completions.parse(
        model=model_deployment_name,
        messages=messages,
        response_format=response_format,
    )
    output_token = completion.usage.completion_tokens
    input_token = completion.usage.prompt_tokens

    print("*" * 50)
    print(completion.usage)
    print("*" * 50)
    event = completion.choices[0].message.parsed
    return event, input_token, output_token
