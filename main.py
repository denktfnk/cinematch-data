from recommender import MovieRecommender

def main():
    print("==================================================")
    print("      CineMatch: Film Öneri Sistemine Hoş Geldiniz!      ")
    print("==================================================")
    
    # Initialize and load data
    recommender = MovieRecommender()
    print("\nVeriler yükleniyor ve model hazırlanıyor. Lütfen bekleyin...\n")
    recommender.build_model()
    
    print("\nSistem Hazır!")
    print("Çıkmak için 'q' veya 'quit' yazabilirsiniz.\n")

    while True:
        user_input = input("Lütfen bir film adı girin (Örn: Toy Story): ").strip()
        
        if user_input.lower() in ['q', 'quit', 'exit']:
            print("CineMatch'i kullandığınız için teşekkürler. Görüşmek üzere!")
            break
            
        if not user_input:
            print("Geçerli bir film adı girmelisiniz.\n")
            continue

        # 1. Kısmi eşleşmeleri bul
        matches = recommender.find_movie_title(user_input)
        
        if not matches:
            print(f"'{user_input}' aramasıyla eşleşen bir film bulunamadı. Lütfen başka bir arama yapın.\n")
            continue
            
        # 2. Tam eşleşme veya seçim
        target_movie = None
        if len(matches) == 1:
            target_movie = matches[0]
            print(f"\nSeçilen Film: {target_movie}")
        else:
            print("\nBirden fazla eşleşme bulundu. Lütfen birini seçin:")
            for i, match in enumerate(matches[:10]): # En fazla 10 eşleşme göster
                print(f"[{i+1}] {match}")
            
            if len(matches) > 10:
                print(f"... ve {len(matches) - 10} film daha.")
                
            selection = input(f"Seçiminiz (1-{min(len(matches), 10)}) veya iptal için 'c': ").strip()
            
            if selection.lower() == 'c':
                print("Seçim iptal edildi.\n")
                continue
                
            try:
                idx = int(selection) - 1
                if 0 <= idx < min(len(matches), 10):
                    target_movie = matches[idx]
                    print(f"\nSeçilen Film: {target_movie}")
                else:
                    print("Geçersiz seçim. İşlem iptal edildi.\n")
                    continue
            except ValueError:
                print("Lütfen geçerli bir sayı girin.\n")
                continue

        # 3. Önerileri al
        try:
            print(f"\n'{target_movie}' için öneriler aranıyor...")
            recommendations = recommender.get_recommendations(target_movie, top_n=5)
            
            if recommendations.empty:
                print("Üzgünüz, bu film için öneri bulunamadı.\n")
                continue
                
            print("\n--------------------------------------------------")
            print(f"Önerilen Filmler (İlk 5):")
            print("--------------------------------------------------")
            
            for i, (_, row) in enumerate(recommendations.iterrows()):
                print(f"{i+1}. {row['title']} (Benzerlik Skoru: {row['similarity_score']:.4f})")
                print(f"   Türler: {row['genres']}")
            
            # 4. Değerlendirme Metriği (Tür Örtüşmesi)
            overlap_score = recommender.evaluate_recommendations(target_movie, recommendations)
            print("\n--------------------------------------------------")
            print(f"Değerlendirme Metriği:")
            print(f"Ortalama Tür Örtüşmesi (Genre Overlap): %{overlap_score:.2f}")
            print("--------------------------------------------------\n")
            
        except ValueError as e:
            print(f"Hata: {e}\n")
        except Exception as e:
            print(f"Beklenmeyen bir hata oluştu: {e}\n")

if __name__ == "__main__":
    main()
