import os
from src.groq_client import MessageAnalyser
from config import groq_config
from tabulate import tabulate


def show_results(analyser, test_messages):
    for i, test_message in enumerate(test_messages, 1):
        print(f"\nMESSAGE {i} : {test_message}")
        analysis_result = analyser.analyse(test_message)
        headers = ["Result Type", "Value", "Confidence"]
        table_data = []
        for result in analysis_result:
            row = [str(result).upper(), analysis_result[result].get('value'), analysis_result[result].get('confidence')]
            table_data.append(row)
        print(tabulate(table_data, headers=headers, tablefmt="pretty"))

    input("\nPress any key to continue...")


def main():
    analyser = MessageAnalyser(groq_config)

    test_messages = [
        "Bu ürünle ilgili çok hayal kırıklığına uğradım. Kalitesi beklediğimden çok daha kötüydü ve müşteri hizmetleri de yardımcı olmadı.",
        "Çok memnun kaldım, teslimat hızlıydı ve ürün beklediğim gibi kaliteli. Herkese tavsiye ederim!",
        "Sipariş ettiğim ürün yanlış geldi. Doğru ürünü göndermenizi rica ediyorum.",
        "Bu toplulukta çok saygısız insanlar var, sürekli küfür ve hakaret ediliyor. Bu durumun bir an önce düzeltilmesi gerek.",
        "Yarın saat 14:00'te toplantımız var. Herkesin zamanında hazır olmasını rica ederim."
    ]

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\nPanoptis mesaj analiz demosuna hoş geldiniz!\n"
              "Lütfen bir seçenek seçin:\n"
              "1 - Hazır mesajları analiz et\n"
              "2 - Kendi mesajınızı girin\n"
              "0 - Çıkış")

        user_input = input("Seçiminiz: ")
        if user_input == '0':
            print("Çıkış yapılıyor... Hoşçakalın!")
            break
        elif user_input == '1':
            show_results(analyser, test_messages)
        elif user_input.lower() == '2':
            user_message = input(
                "Lütfen analiz etmek istediğiniz cümleyi yazın (birden fazla cümle için '-' kullanın): ")
            if user_message.strip():
                user_messages = [msg.strip() for msg in user_message.split('-')]
                show_results(analyser, user_messages)
        else:
            print("Geçersiz seçenek, lütfen tekrar deneyin.")


if __name__ == "__main__":
    main()
