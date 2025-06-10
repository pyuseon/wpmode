


def split_urls_to_files(input_file_path, batch_size=300):
    """
    URL 파일을 읽어서 지정된 개수씩 나누어 별도 파일로 저장

    Args:
        input_file_path (str): 입력 파일 경로
        batch_size (int): 각 파일에 저장할 URL 개수 (기본값: 300)
        output_prefix (str): 출력 파일명 접두사
    """
    try:
        # 입력 파일 읽기
        with open(input_file_path, 'r', encoding='utf-8') as file:
            urls = [line.strip() for line in file if line.strip()]

        print(f"총 {len(urls)}개의 URL을 발견했습니다.")

        # URL을 배치 크기별로 나누기
        batches = [urls[i:i + batch_size] for i in range(0, len(urls), batch_size)]

        print(f"{len(batches)}개의 파일로 분할됩니다.")

        # 출력 파일명 접두사 설정
        input_file_name = input_file_path.split("/")[-1].replace(".txt", "")  # 파일명만 추출
        output_prefix = input_file_name + "_batch"

        # 각 배치를 별도 파일로 저장
        for i, batch in enumerate(batches, 1):
            output_filename = f"{output_prefix}_{i:03d}.txt"

            with open(output_filename, 'w', encoding='utf-8') as output_file:
                for url in batch:
                    output_file.write(url + '\n')

            print(f"{output_filename} 저장 완료 ({len(batch)}개 URL)")

        print("\n분할 작업이 완료되었습니다!")

        # 요약 정보 출력
        print(f"\n=== 분할 요약 ===")
        print(f"원본 URL 개수: {len(urls)}")
        print(f"생성된 파일 수: {len(batches)}")
        print(f"배치 크기: {batch_size}")

        return batches

    except FileNotFoundError:
        print(f"오류: '{input_file_path}' 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
#
#
# def split_urls_from_text(url_text, batch_size=300, output_prefix="parental_leave_batch"):
#     """
#     텍스트에서 직접 URL을 추출하여 분할 저장
#
#     Args:
#         url_text (str): URL이 포함된 텍스트
#         batch_size (int): 각 파일에 저장할 URL 개수
#         output_prefix (str): 출력 파일명 접두사
#     """
#     # 텍스트에서 URL 추출 (줄 단위로)
#     urls = [line.strip() for line in url_text.split('\n') if line.strip() and line.strip().startswith('https://')]
#
#     print(f"총 {len(urls)}개의 URL을 발견했습니다.")
#
#     # URL을 배치 크기별로 나누기
#     batches = [urls[i:i + batch_size] for i in range(0, len(urls), batch_size)]
#
#     print(f"{len(batches)}개의 파일로 분할됩니다.")
#
#     # 각 배치를 별도 파일로 저장
#     for i, batch in enumerate(batches, 1):
#         output_filename = f"{output_prefix}_{i:03d}.txt"
#
#         with open(output_filename, 'w', encoding='utf-8') as output_file:
#             for url in batch:
#                 output_file.write(url + '\n')
#
#         print(f"{output_filename} 저장 완료 ({len(batch)}개 URL)")
#
#     print("\n분할 작업이 완료되었습니다!")
#
#     # 요약 정보 출력
#     print(f"\n=== 분할 요약 ===")
#     print(f"원본 URL 개수: {len(urls)}")
#     print(f"생성된 파일 수: {len(batches)}")
#     print(f"배치 크기: {batch_size}")
#
#     return batches


if __name__ == "__main__":
    # 예시: 파일에서 URL 분할
    split_urls_to_files("childbirth.txt", batch_size=300)

    # 예시: 텍스트에서 URL 분할
    example_text = """
    https://example.com/news1
    https://example.com/news2
    https://example.com/news3
    """
    # split_urls_from_text(example_text, batch_size=300, output_prefix="parental_leave_batch")