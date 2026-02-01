#!/usr/bin/env python3
"""
XML構造検証スクリプト

PubMedから実際のXMLを取得し、その構造を詳細に表示して、
xml_extractorの実装が正しいかを確認します。
"""

import sys
from xml.etree.ElementTree import tostring

from pymed_paperscraper import PubMed

# Add parent directory to path to import ppget modules
sys.path.insert(0, "/Users/masaki/dev/ppget")
# Note: extract_article_doi_from_xml is no longer used as pymed-paperscraper 1.0.5+
# correctly handles DOI extraction


def print_element_tree(element, indent=0, max_depth=5):
    """XML要素のツリー構造を表示"""
    if indent > max_depth:
        return

    prefix = "  " * indent

    # 要素名と属性を表示
    attrs = " ".join([f'{k}="{v}"' for k, v in element.attrib.items()])
    if attrs:
        print(f"{prefix}<{element.tag} {attrs}>")
    else:
        print(f"{prefix}<{element.tag}>")

    # テキストコンテンツを表示（最初の50文字まで）
    if element.text and element.text.strip():
        text = element.text.strip()[:50].replace("\n", "\\n")
        print(f"{prefix}  TEXT: {text}...")

    # 子要素を再帰的に表示
    for child in element:
        print_element_tree(child, indent + 1, max_depth)


def inspect_xml_structure(pubmed_id: str):
    """指定されたPubMed IDの記事のXML構造を調査"""
    print(f"\n{'=' * 80}")
    print(f"PubMed ID: {pubmed_id}")
    print(f"{'=' * 80}\n")

    pubmed = PubMed(tool="ppget-test", email="test@example.com")
    results = pubmed.query(pubmed_id, max_results=1)

    for article in results:
        xml_element = getattr(article, "xml", None)

        if xml_element is None:
            print("ERROR: XML要素が取得できませんでした")
            return

        print("\n--- FULL XML TREE ---")
        print_element_tree(xml_element, max_depth=4)

        # pymed-paperscraperが取得したデータ
        print("\n--- PYMED-PAPERSCRAPER EXTRACTED DATA ---")
        print(f"Title: {getattr(article, 'title', None)}")
        abstract = getattr(article, "abstract", None)
        abstract_preview = abstract[:100] if abstract else None
        print(f"Abstract: {abstract_preview}...")
        print(f"Journal: {getattr(article, 'journal', None)}")
        print(f"DOI: {getattr(article, 'doi', None)}")

        # XPath検証
        print("\n--- XPATH VALIDATION ---")

        # ArticleTitle
        title_elements = xml_element.findall(".//ArticleTitle")
        print(f"\nArticleTitle elements found: {len(title_elements)}")
        for i, elem in enumerate(title_elements):
            print(f"  [{i}] Tag: {elem.tag}")
            print(f"      Attributes: {elem.attrib}")
            print(f"      Text (elem.text): {elem.text}")
            print(f"      Full text (itertext): {''.join(elem.itertext())}")
            print(f"      Children: {[child.tag for child in elem]}")

        # AbstractText
        abstract_elements = xml_element.findall(".//AbstractText")
        print(f"\nAbstractText elements found: {len(abstract_elements)}")
        for i, elem in enumerate(abstract_elements):
            print(f"  [{i}] Tag: {elem.tag}")
            print(f"      Attributes: {elem.attrib}")
            print(f"      Label: {elem.get('Label')}")
            print(f"      Text (elem.text): {elem.text[:50] if elem.text else None}...")
            print(f"      Full text (itertext): {''.join(elem.itertext())[:50]}...")
            print(f"      Children: {[child.tag for child in elem]}")

        # Journal/Title
        journal_elements = xml_element.findall(".//Journal/Title")
        print(f"\nJournal/Title elements found: {len(journal_elements)}")
        for i, elem in enumerate(journal_elements):
            print(f"  [{i}] Tag: {elem.tag}")
            print(f"      Text: {elem.text}")
            print(f"      Full text (itertext): {''.join(elem.itertext())}")

        # DOI
        doi_elements = xml_element.findall(".//ArticleId[@IdType='doi']")
        print(f"\nArticleId[@IdType='doi'] elements found: {len(doi_elements)}")
        for i, elem in enumerate(doi_elements):
            print(f"  [{i}] Tag: {elem.tag}")
            print(f"      Attributes: {elem.attrib}")
            print(f"      Text: {elem.text}")
            print(f"      Full text (itertext): {''.join(elem.itertext())}")

        # すべてのArticleId要素も確認
        all_article_ids = xml_element.findall(".//ArticleId")
        print(f"\nAll ArticleId elements found: {len(all_article_ids)}")
        for i, elem in enumerate(all_article_ids):
            print(f"  [{i}] IdType: {elem.get('IdType')}, Text: {elem.text}")

        # DOI extraction (using pymed-paperscraper 1.0.5+)
        print("\n--- DOI EXTRACTION TEST ---")
        doi_attr = getattr(article, "doi", "")
        print(f"pymed-paperscraper DOI (raw): {doi_attr}")
        # Check for newlines in DOI
        if doi_attr and chr(10) in doi_attr:
            first_line_doi = doi_attr.split(chr(10))[0]
            print(f"DOI (first line only): {first_line_doi}")
            print("WARNING: DOI contains newline characters")

        # Raw XML出力（デバッグ用）
        print("\n--- RAW XML (first 2000 chars) ---")
        raw_xml = tostring(xml_element, encoding="unicode")
        print(raw_xml[:2000])

        break  # 最初の1件のみ処理


def main():
    """メイン処理"""
    # テスト用のPubMed ID
    # これらは異なる特徴を持つ記事を選択しています
    test_cases = [
        ("38053300", "構造化アブストラクト、イタリック体を含むタイトル"),
        ("33037426", "一般的な記事"),
        ("39523223", "最近の記事"),
    ]

    print("PubMed XML構造検証")
    print("==================\n")
    print("このスクリプトはPubMedから実際のXMLを取得し、")
    print("xml_extractorの実装が正しいかを確認します。\n")

    if len(sys.argv) > 1:
        # コマンドライン引数でPubMed IDが指定された場合
        pubmed_id = sys.argv[1]
        inspect_xml_structure(pubmed_id)
    else:
        # デフォルトのテストケースを実行
        for pubmed_id, description in test_cases:
            print(f"\nTest case: {description}")
            inspect_xml_structure(pubmed_id)
            print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
