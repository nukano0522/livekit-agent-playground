import chromadb
import json
import os
from typing import List, Dict, Any
from openai import OpenAI, AzureOpenAI
from dotenv import load_dotenv

# 環境変数をクリアして.envファイルから再読み込み
env_vars_to_clear = [
    "OPENAI_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_ENDPOINT",
    "OPENAI_API_VERSION",
    "AZURE_OPENAI_ENDPOINT_EM",
    "AZURE_OPENAI_API_KEY_EM",
    "OPENAI_API_VERSION_EM"
]

for var in env_vars_to_clear:
    if var in os.environ:
        del os.environ[var]

# .envファイルを強制的に再読み込み
load_dotenv(override=True)

class ChromaDBInitializer:
    def __init__(self, collection_name: str = "livekit_knowledge"):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection_name = collection_name
        
        # Embedding用のAzure OpenAI APIキーが設定されている場合はそれを使用
        if os.environ.get("AZURE_OPENAI_API_KEY_EM") and os.environ.get("AZURE_OPENAI_ENDPOINT_EM"):
            self.openai_client = AzureOpenAI(
                api_key=os.environ.get("AZURE_OPENAI_API_KEY_EM"),
                api_version=os.environ.get("OPENAI_API_VERSION_EM", "2024-08-01-preview"),
                azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT_EM")
            )
            self.embedding_model = os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            print(f"Azure OpenAI API (Embedding専用)を使用してembeddingを生成します (モデル: {self.embedding_model})")
        # 通常のAzure OpenAI APIキーが設定されている場合
        elif os.environ.get("AZURE_OPENAI_API_KEY") and os.environ.get("AZURE_OPENAI_ENDPOINT"):
            self.openai_client = AzureOpenAI(
                api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
                api_version=os.environ.get("OPENAI_API_VERSION", "2024-08-01-preview"),
                azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
            )
            self.embedding_model = os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            print(f"Azure OpenAI APIを使用してembeddingを生成します (モデル: {self.embedding_model})")
        else:
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.embedding_model = "text-embedding-3-small"
            print("OpenAI APIを使用してembeddingを生成します")
        
    def reset_collection(self):
        """既存のコレクションを削除して再作成"""
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"既存のコレクション '{self.collection_name}' を削除しました")
        except:
            print(f"コレクション '{self.collection_name}' は存在しません")
        
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"新しいコレクション '{self.collection_name}' を作成しました")
    
    def get_embedding(self, text: str) -> List[float]:
        """OpenAI APIを使用してテキストのembeddingを取得"""
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
    def prepare_documents(self, knowledge_base: Dict[str, Any]) -> List[Dict[str, Any]]:
        """知識ベースをドキュメント形式に変換"""
        documents = []
        
        # 会社情報
        company = knowledge_base.get('company_info', {})
        company_text = f"""
        会社名: {company.get('name')}
        設立: {company.get('founded')}
        本社: {company.get('headquarters')}
        従業員数: {company.get('employees')}
        サービス: {', '.join(company.get('services', []))}
        """
        documents.append({
            "id": "company_info",
            "text": company_text.strip(),
            "metadata": {"category": "company_info", "type": "general"}
        })
        
        # 製品情報
        for i, product in enumerate(knowledge_base.get('products', [])):
            product_text = f"""
            製品名: {product['name']}
            説明: {product['description']}
            """
            if 'features' in product:
                product_text += f"\n機能: {', '.join(product['features'])}"
            if 'pricing' in product:
                product_text += f"\n価格: {product['pricing']}"
            if 'supported_models' in product:
                product_text += f"\n対応モデル: {', '.join(product['supported_models'])}"
            if 'use_cases' in product:
                product_text += f"\nユースケース: {', '.join(product['use_cases'])}"
            
            documents.append({
                "id": f"product_{i}_{product['name'].replace(' ', '_')}",
                "text": product_text.strip(),
                "metadata": {
                    "category": "product",
                    "product_name": product['name'],
                    "type": "product_detail"
                }
            })
        
        # 技術仕様
        tech = knowledge_base.get('technical_specs', {})
        tech_text = f"""
        プロトコル: {', '.join(tech.get('protocols', []))}
        対応プラットフォーム: {', '.join(tech.get('supported_platforms', []))}
        プログラミング言語: {', '.join(tech.get('programming_languages', []))}
        最大参加者数/ルーム: {tech.get('max_participants_per_room')}
        レイテンシ: {tech.get('latency')}
        """
        documents.append({
            "id": "technical_specs",
            "text": tech_text.strip(),
            "metadata": {"category": "technical", "type": "specifications"}
        })
        
        # サポート情報
        support = knowledge_base.get('support', {})
        support_text = f"""
        ドキュメント: {support.get('documentation')}
        コミュニティ: {support.get('community')}
        エンタープライズサポート: {support.get('enterprise')}
        """
        documents.append({
            "id": "support_info",
            "text": support_text.strip(),
            "metadata": {"category": "support", "type": "support_info"}
        })
        
        return documents
    
    def insert_documents(self, documents: List[Dict[str, Any]]):
        """ドキュメントをChromaDBに挿入"""
        ids = []
        embeddings = []
        texts = []
        metadatas = []
        
        print("ドキュメントのembeddingを生成中...")
        for doc in documents:
            ids.append(doc["id"])
            texts.append(doc["text"])
            metadatas.append(doc["metadata"])
            embedding = self.get_embedding(doc["text"])
            embeddings.append(embedding)
            print(f"  - {doc['id']} のembeddingを生成しました")
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        print(f"\n{len(documents)}件のドキュメントをChromaDBに登録しました")
    
    def verify_collection(self):
        """コレクションの内容を確認"""
        count = self.collection.count()
        print(f"\nコレクション '{self.collection_name}' には {count} 件のドキュメントが含まれています")
        
        # サンプルクエリでテスト
        test_query = "LiveKit Cloudの価格を教えてください"
        embedding = self.get_embedding(test_query)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=3
        )
        
        print(f"\nテストクエリ: '{test_query}'")
        print("検索結果:")
        for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
            print(f"  {i+1}. (距離: {distance:.4f})")
            print(f"     {doc[:100]}...")


def main():
    # 初期化
    initializer = ChromaDBInitializer()
    
    # コレクションをリセット
    initializer.reset_collection()
    
    # 使用するデータファイルを選択
    data_file = 'test_data_extended.json' if os.path.exists('test_data_extended.json') else 'test_data.json'
    print(f"データファイル '{data_file}' を使用します")
    
    # 知識ベースを読み込む
    with open(data_file, 'r', encoding='utf-8') as f:
        knowledge_base = json.load(f)
    
    # ドキュメントを準備
    documents = initializer.prepare_documents(knowledge_base)
    
    # 追加のドキュメントを作成（拡張データの場合）
    if data_file == 'test_data_extended.json':
        # 価格詳細
        if 'pricing_details' in knowledge_base:
            pricing = knowledge_base['pricing_details']['cloud']
            pricing_text = f"""
            LiveKit Cloud価格詳細:
            音声通話: {pricing.get('audio')}/分
            ビデオ通話: {pricing.get('video')}/分
            録画: {pricing.get('recording')}/分
            ストリーミング: {pricing.get('streaming')}/分
            帯域幅: {pricing.get('bandwidth')}/GB
            """
            documents.append({
                "id": "pricing_details",
                "text": pricing_text.strip(),
                "metadata": {"category": "pricing", "type": "detailed_pricing"}
            })
        
        # 統合サービス
        if 'integrations' in knowledge_base:
            for integration in knowledge_base['integrations']:
                integration_text = f"""
                {integration['category']}カテゴリの統合:
                対応サービス: {', '.join(integration['services'])}
                """
                documents.append({
                    "id": f"integration_{integration['category']}",
                    "text": integration_text.strip(),
                    "metadata": {"category": "integration", "integration_type": integration['category']}
                })
        
        # ケーススタディ
        if 'case_studies' in knowledge_base:
            for i, case in enumerate(knowledge_base['case_studies']):
                case_text = f"""
                導入事例: {case['company']}
                業界: {case['industry']}
                ユースケース: {case['use_case']}
                成果: {case['results']}
                """
                documents.append({
                    "id": f"case_study_{i}",
                    "text": case_text.strip(),
                    "metadata": {"category": "case_study", "industry": case['industry']}
                })
    
    # ChromaDBに挿入
    initializer.insert_documents(documents)
    
    # 確認
    initializer.verify_collection()
    
    print("\nChromaDBの初期化が完了しました！")


if __name__ == "__main__":
    main()