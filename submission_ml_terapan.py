# -*- coding: utf-8 -*-
"""sysres - Copy (2).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/114yKbSQfqYEI3JeeWlpa8onMiYbCvaEp

# Identitas & Definisi Hasil Pekerjaan
## Ivan Budianto

### shinsuketenma0603@gmail.com
### Submission Machine Learning Terapan 2

## Sistem Rekomendasi Judul Anime 

### Metode:
- Collaborative filtering
- Hypertuning menggunakan SGD optimizer & learning rate

Melakukan import library yang dibutuhkan (Pandas, Numpy, Tensorflow)
"""

import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.preprocessing import MinMaxScaler

import os

"""# Pre-Processing

## Berikut adalah langkah-langkah yang saya lakukan dalam proses preprocessing data:
1. Memasukkan dataset data review user 
2. Melakukan filtering data untuk mencari hanya user yang sudah menonton (mereview tentunya) setidaknya 500 anime 
3. Melakukan filtering data duplikat
4. Scaling dataset pada rating menggunakan minmaxscaler
5. Encode anime dan user
6. Proses shuffling dan pendefinisian fitur (x dan y)
7. Proses split dataset
8. Ekstrak fitur berupa parameter untuk melakukan pemodelan

## Memasukkan dataset data review user 
Dari dataset mengenai rating anime oleh user, hanya menggunakan beberapa kolom saja (slicing) pada kolom user_id, anime_id, dan rating pengguna untuk setiap anime.
"""

#mendefinisikan base_dir, dan memasukkan dataset

base_dir = "C:/Users/xcessive/Documents/machine_learning"

df_raw = pd.read_csv(os.path.join(base_dir, 'animelist.csv'),
                     usecols=["user_id", "anime_id", "rating"])

df_raw.head()

"""## Melakukan filtering data untuk mencari hanya user yang sudah menonton (mereview tentunya) setidaknya 500 anime 
Dari dataset yang telah diimport, sekarang akan dilakukan filtering untuk mencari user-user yang telah mereview setidaknya 500 anime, dan meletakkan data tersebut pada user_rating_df.
"""

#filtering data user

n_ratings = df_raw['user_id'].value_counts()
user_rating_df = df_raw[df_raw['user_id'].isin(n_ratings[n_ratings >= 500].index)].copy()

"""## Melakukan filtering data duplikat
Duplikasi data akan menyebabkan hasil dari sistem rekomendasi menjadi "offside". Maka dari itu, perlu dilakukan filtering pada dataset yang digunakan pada data yang duplikat atau sama.
"""

#filtering data duplikat

duplicates = user_rating_df.duplicated()
user_rating_df = user_rating_df[~duplicates]

print("User in use: {}".format(len(df_raw['user_id'].unique())))

"""## Scaling dataset pada rating menggunakan minmaxscaler
Dataset yang besar, dan memiliki range yang tinggi akan menyulitkan algoritma dalam melakukan tugasnya (membuat rekomendasi). Dengan penggunaan MinMaxScaler dari sklearn, akan memudahkan dalam melakukan pemrosesan data. Kolom yang akan discaling adalah kolom rating.
"""

# scaling dataset

minmax_scaler = MinMaxScaler()
user_rating_df[["rating"]] = minmax_scaler.fit_transform(user_rating_df[["rating"]])

user_rating_df

"""## Encode anime dan user
Proses encode akan memudahkan program dalam mengidentifikasi setiap data yang ada. Melalui proses encode ini, program dapat dengan mudah mengenali setiap user dan anime yang ada melalui bilangan numerik, sehingga pemrosesan data dapat dilakukan dengan lebih efisien.
"""

user_ids = user_rating_df["user_id"].unique().tolist()
user2user_encoded = {x: i for i, x in enumerate(user_ids)}
user_encoded2user = {i: x for i, x in enumerate(user_ids)}
user_rating_df["user"] = user_rating_df["user_id"].map(user2user_encoded)
n_users = len(user2user_encoded)

anime_ids = user_rating_df["anime_id"].unique().tolist()
anime2anime_encoded = {x: i for i, x in enumerate(anime_ids)}
anime_encoded2anime = {i: x for i, x in enumerate(anime_ids)}
user_rating_df["anime"] = user_rating_df["anime_id"].map(anime2anime_encoded)
n_animes = len(anime2anime_encoded)

print("Num of users: {}, Num of animes: {}".format(n_users, n_animes))
print("Min rating: {}, Max rating: {}".format(min(user_rating_df['rating']), max(user_rating_df['rating'])))

"""## Proses shuffling dan pendefinisian fitur (x dan y)

Melakukan shuffling dari data pada dataset untuk menghindari overfitting dari model. Dengan melakukan shuffling, model akan belajar dengan lebih "obyektif"

Mendefinisikan X dan y, dimana:
- X merupakan data yang menjadi tolok ukur untuk prediksi (data dari dataset)
- y merupakan hasil atau tujuan dari hasil prediksinya
"""

#shuffle data

user_rating_df = user_rating_df.sample(frac=1, random_state=73)

X = user_rating_df[['user', 'anime']].values
y = user_rating_df["rating"]

"""## Proses split dataset
Sebagai persiapan sebelum melakukan pemodelan, perlu dilakukan pemisahan dataset train dan test. Pemisahan ini berguna untuk melakukan validasi keakuratan dari data yang telah ditraining. Dalam kasus kali ini, saya memisahkan dataset test sebanyak 20ribu data, dan data sisanya merupakan dataset traning.

Pemisahkan antara dataset latihan (train) dan 
dataset test (test) dengan pembagian:
- 20000 (20ribu) dataset pengujian (test set)
- sisanya merupakan dataset latihan (train set)
"""

# Split
test_set = 20000
train_indices = user_rating_df.shape[0] - test_set 

X_train, X_test, y_train, y_test = (
    X[:train_indices],
    X[train_indices:],
    y[:train_indices],
    y[train_indices:],
)

"""## Ekstrak fitur berupa parameter untuk melakukan pemodelan
Dalam melakukan pelatihan model, tentu dibutuhkan sebuah data yang digunakan untuk melakukan pelatihan.
"""

X_train_params = [X_train[:, 0], X_train[:, 1]]
X_test_params = [X_test[:, 0], X_test[:, 1]]

"""# Modelling

Pembuatan model menggunakan 2 metode, yaitu:
- Collaborative Filtering
- Pengembangan Model Pertama (Hypertuning Collaborative Filtering)

Berikut adalah langkah-langkah yang saya lakukan dalam proses modelling:
1. Instantiasi Model pertama
2. Membuat Callback untuk kedua model
3. Melakukan proses training pada model pertama
4. Hasil training, dan verdict #1
5. Menyimpan model (bobot hasil pelatihan) pertama pada JSON
6. Mendefinisikan model ke-2
7. Melakukan proses training pada model kedua
8. Hasil training, dan verdict #2
9. Menyimpan model (bobot hasil pelatihan) kedua pada JSON

## Mendefinisikan model & parameter yang digunakan pada model pertama
Mendefinisikan model, dan metode yang digunakan, yaitu model RecommenderNet pertama dari Tensoflow sebagai base dari model berikutnya. Model ini menggunakan parameter yang telah kita telusuri bersama sebelumnya pada parameter X untuk melakukan training dan testing.

Dalam model pertama, optimizer yang digunakan adalah Adam, dimana optimizer ini merupakan optimizer yang "all-round", dan dapat menyelesaikan hampir seluruh masalah dalam machine learning dengan baik. Maka dari itu, dipilih Adam sebagai optimizer pertama.

Metrik yang digunakan dalam pemodelan ini adalah mae dan mse, dimana dalam modul dicoding juga menggunakan metrik mse untuk melakukan training model serupa. Penjelasan lebih lanjut mengenai metrik evaluasi akan dijelaskan pada bagian evaluasi.
"""

def RecommenderNet():
    embedding_size = 128
    
    user = tf.keras.layers.Input(name = 'user', shape = [1])
    user_embedding = tf.keras.layers.Embedding(name = 'user_embedding',
                       input_dim = n_users, 
                       output_dim = embedding_size)(user)
    
    anime = tf.keras.layers.Input(name = 'anime', shape = [1])
    anime_embedding = tf.keras.layers.Embedding(name = 'anime_embedding',
                       input_dim = n_animes, 
                       output_dim = embedding_size)(anime)
    
    res = tf.keras.layers.Dot(name = 'dot_product', normalize = True, axes = 2)([user_embedding, anime_embedding])
    res = tf.keras.layers.Flatten()(res)
        
    res = tf.keras.layers.Dense(1, kernel_initializer='he_normal')(res)
    res = tf.keras.layers.BatchNormalization()(res)
    res = tf.keras.layers.Activation("sigmoid")(res)
    
    model = tf.keras.models.Model(inputs=[user, anime], outputs=res)
    model.compile(loss='binary_crossentropy', metrics=["mae", "mse"], optimizer='Adam')
    
    return model

"""## Instantiasi Model pertama

Dari model RecommenderNet yang telah berhasil dicompile, berikut adalah proses instantiasi dari model pertama dengan memanggil model tersebut.
"""

model = RecommenderNet()

"""## Membuat Callback untuk kedua model

Callback yang digunakan disini adalah callback bawaan dari Keras, yaitu Early Stopping. Early Stopping, seperti namanya, akan menghentikan proses converge model yang sedang dilatih lebih cepat dari seharusnya. Penghentian ini akan bergantung pada learning rate dari model pada beberapa epoch. Bila epoch dirasa "merugikan" dari sisi akurasi yang tidak bertambah, atau malah berkurang, maka proses training akan dihentikan.
"""

early_stopping = tf.keras.callbacks.EarlyStopping(patience = 3, monitor='val_loss', 
                               mode='min', restore_best_weights=True)

"""## Melakukan proses training pada model pertama
Melakukan proses training (fitting) pada model pertama menggunakan dataset yang telah didefinisikan. Proses ini dilakukan menggunakan syntax fit pada model.
"""

# Model training
history = model.fit(
    x=X_train_params,
    y=y_train,
    batch_size=10000,
    epochs=20,
    verbose=1,
    validation_data=(X_test_params, y_test),
    callbacks=early_stopping
)

"""## Hasil training, dan verdict #1

Dari hasil training yang telah dilakukan, didapatkan hasil yang sangat baik, dimana mse sudah berada dibawah angka 0.05. Dari hasil pelatihan ini, model dapat melakukan prediksi dari data train dan test dengan cukup baik, dimana tidak ada perbedaan yang signifikan antara MAE & MSE pada train dan val.
Hasil yang baik juga dapat dilihat pada variabel loss, dimana loss pada proses training cenderung mengalami penurunan.

Untuk memperjelas hasil dari pelatihan ini, berikut adalah grafik plotting loss & val loss untuk model pertama.
"""

# Commented out IPython magic to ensure Python compatibility.
#Training results
import matplotlib.pyplot as plt
# %matplotlib inline

plt.plot(history.history["loss"][0:-2])
plt.plot(history.history["val_loss"][0:-2])
plt.title("model loss")
plt.ylabel("loss")
plt.xlabel("epoch")
plt.legend(["train", "test"], loc="upper left")
plt.show()

"""## Menyimpan model (bobot hasil pelatihan) pertama pada JSON
Dengan melakukan penyimpanan bobot dari model yang telah dibuat, kita dapat mengakses model tersebut dengan akurasi yang sama tanpa perlu melakukan training kembali dan memiliki resiko untuk menghasilkan akurasi yang berbeda dari model sebelumnya. Untuk melakukan hal ini, kita hanya perlu mengimport modul model_from_json, dan mengeksekusi query berikut.
"""

from keras.models import model_from_json

model_json = model.to_json()

with open("model.json", "w") as json_file:
    json_file.write(model_json)

model.save_weights("model.h5")
print("Model saved")

# #mengambil model
# json_file = open('model.json', 'r')
# saved_model = json_file.read()
# # close the file as good practice
# json_file.close()
# model_from_json = model_from_json(saved_model)
# # load weights into new model
# model_from_json.load_weights("model.h5")
# print("Model loaded")

"""## Mendefinisikan model ke-2

Dalam model pertama, optimizer yang digunakan adalah Adam, dimana optimizer ini merupakan optimizer yang "all-round", dan dapat menyelesaikan hampir seluruh masalah dalam machine learning dengan baik. Maka dari itu, dipilih Adam sebagai optimizer pertama.

Dalam model kedua ini, algoritma yang digunakan merupakan hypertuning secara manual dengan menggunakan optimizer yang berbeda. Dengan menggunakan optimizer yang berbeda, kita dapat mendapatkan algoritma "berbeda". Disini, digunakan Stocasthic Gradient Descent atau SGD optimizer untuk melakukan optimizing pada model.
Selain itu, dalam model ini juga diubah parameter embedding_size menjadi 2x lipat dari model sebelumnya.

Metrik yang digunakan dalam pemodelan ini adalah mae dan mse, dimana dalam model sebelumnya juga menggunakan parameter yang sama. Penggunaan parameter yang sama ditujukan agar dalam pembuatan model dapat dinilai secara objektif dari kedua sisinya.
"""

optimizer = tf.keras.optimizers.SGD(learning_rate=1.0000e-04, momentum=0.9)

def RecommenderNet():
    embedding_size = 256
    initializer = tf.keras.initializers.RandomNormal(mean=0., stddev=1.)
    
    user = tf.keras.layers.Input(name = 'user', shape = [1])
    user_embedding = tf.keras.layers.Embedding(name = 'user_embedding',
                       input_dim = n_users, 
                       output_dim = embedding_size)(user)
    
    anime = tf.keras.layers.Input(name = 'anime', shape = [1])
    anime_embedding = tf.keras.layers.Embedding(name = 'anime_embedding',
                       input_dim = n_animes, 
                       output_dim = embedding_size)(anime)
    
    res = tf.keras.layers.Dot(name = 'dot_product', normalize = True, axes = 2)([user_embedding, anime_embedding])
    res = tf.keras.layers.Flatten()(res)
    
    res = tf.keras.layers.Dense(1, kernel_initializer=initializer)(res)
    res = tf.keras.layers.BatchNormalization()(res)
    res = tf.keras.layers.Activation("sigmoid")(res)
    
    model = tf.keras.models.Model(inputs=[user, anime], outputs=res)
    model.compile(loss='binary_crossentropy', metrics=["mae", "mse"], optimizer=optimizer)
    
    return model

"""## Melakukan proses training pada model kedua
Melakukan proses training (fitting) pada model kedua menggunakan dataset yang sama. Proses ini dilakukan menggunakan syntax fit pada model.
"""

# Model training 2
model_hyper = RecommenderNet()
history_hyper = model_hyper.fit(
    x=X_train_params,
    y=y_train,
    batch_size=10000,
    epochs=20,
    verbose=1,
    validation_data=(X_test_params, y_test),
    callbacks=early_stopping
)

"""## Hasil training, dan verdict #2

Dari hasil training yang telah dilakukan, didapatkan hasil yang biasa saja, dimana mse sudah berada dibawah angka 0.5. Dari hasil pelatihan ini, model dapat melakukan prediksi dari data train dan test dengan cukup baik, dimana tidak ada perbedaan yang signifikan antara MAE & MSE pada train dan val.
Namun, bila dibandingkan dengan model pertama, ternyata pengembangan model menggunakan SGD tidak sebaik dengan menggunakan Adam. Dari sini, dapat dilihat melalui akurasi dari model yang didapat.

Untuk memperjelas hasil dari pelatihan ini, berikut adalah grafik plotting loss & val loss untuk model kedua.
"""

# Commented out IPython magic to ensure Python compatibility.
#Training results
import matplotlib.pyplot as plt
# %matplotlib inline

plt.plot(history_hyper.history["loss"][0:-2])
plt.plot(history_hyper.history["val_loss"][0:-2])
plt.title("model loss")
plt.ylabel("loss")
plt.xlabel("epoch")
plt.legend(["train", "test"], loc="upper left")
plt.show()

"""## Menyimpan model (bobot hasil pelatihan) kedua pada JSON
Sama seperti proses sebelumnya, dilakukan penyimpanan bobot dari model kedua pada JSON.
"""

from keras.models import model_from_json

model_hyper_json = model_hyper.to_json()

with open("model_hyper.json", "w") as json_file:
    json_file.write(model_hyper_json)

model_hyper.save_weights("model_hyper.h5")
print("Model saved")

# #mengambil model
# json_file = open('model_hyper.json', 'r')
# saved_model = json_file.read()
# # close the file as good practice
# json_file.close()
# model_from_json = model_from_json(saved_model)
# # load weights into new model
# model_from_json.load_weights("model_hyper.h5")
# print("Model loaded")

"""# Exhibition rekomendasi anime
Dalam proses ini, kita akan melakukan ekstraksi hasil pelatihan dari model yang telah dibangun untuk memberikan N rekomendasi anime yang diinginkan oleh user. Dalam latihan ini, digunakan maksimal 10 anime sebagai rekomendasi untuk user setelah melakukan input berupa judul berbahasa inggris dari anime yang diinginkan.

Proses tersebut terdiri dari beberapa bagian, yaitu:
1. Mengambil bobot dari tiap anime yang berhasil ditraining
2. Mengambil data dari dataset anime kedalam dataframe baru
3. Mencari nama anime dari dataframe
4. Melakukan sorting dari skor, merapikan dataframe
5. Pengambilan metadata anime dari dataframe (df)
6. Mendefinisikan fungsi untuk eksekusi dari model #1
7. Mendefinisikan fungsi untuk eksekusi dari model #2
8. Testing model #1 untuk anime "Naruto" untuk menampilkan 10 anime termirip.
9. Testing model #2 untuk anime "Naruto" untuk menampilkan 10 anime termirip.

## Mengambil bobot dari tiap anime yang berhasil ditraining
Dari kedua model yang telah berhasil ditraining, hasil dari kedua traning berupa bobot akan diekstrak dari model untuk melakukan prediksi berupa pemberian rekomendasi kepada pengguna berdasarkan judul anime yang dimasukkan.

Terdapat 2 fungsi yang dibuat dalam tahap ini, yaitu:
- Fungsi extract_weights yang membutuhkan parameter berupa nama anime yang berasal dari model pertama
- Fungsi extract_weights_hyper yang membutuhkan parameter berupa nama anime yang berasal dari model kedua
"""

def extract_weights(name, model):
    weight_layer = model.get_layer(name)
    weights = weight_layer.get_weights()[0]
    weights = weights / np.linalg.norm(weights, axis = 1).reshape((-1, 1))

    return weights

anime_weights = extract_weights('anime_embedding', model)
user_weights = extract_weights('user_embedding', model)

def extract_weights_hyper(name, model_hyper):
    weight_layer = model_hyper.get_layer(name)
    weights = weight_layer.get_weights()[0]
    weights = weights / np.linalg.norm(weights, axis = 1).reshape((-1, 1))

    return weights

anime_weights_hyper = extract_weights_hyper('anime_embedding', model_hyper)
user_weights_hyper = extract_weights_hyper('user_embedding', model_hyper)

"""## Mengambil data dari dataset anime kedalam dataframe baru

Untuk memperlihatkan hasil yang dapat dinilai secara mudah, maka dibuatlah sebuah dataframe baru untuk menunjang pengambilan data.
"""

df = pd.read_csv(base_dir + '/anime.csv', low_memory=True)
df = df.replace("Unknown", np.nan)

"""## Mencari nama anime dari dataframe

Untuk mendapatkan nama dari dataframe anime, dibutuhkan slicing pada kolom nama. Namun, karena terdapat judul yang merupakan hasil dari translate (misal "Shingeki no Kyojin" menjadi "Attack On Titan"), maka dibutuhkan nama anime yang universal. Maka dari itu, diambil judul inggris dari anime tersebut untuk dijadikan parameter baru.
Apabila tidak memiliki judul berbahasa inggris, maka judul original akan digunakan.
"""

def get_anime_name(anime_id):
    try:
        name = df[df.anime_id == anime_id].eng_version.values[0]
        if name is np.nan:
            name = df[df.anime_id == anime_id].Name.values[0]
    except:
        print('error')
    
    return name

df['anime_id'] = df['MAL_ID']
df["eng_version"] = df['English name']
df['eng_version'] = df.anime_id.apply(lambda x: get_anime_name(x))

df.head(5)

"""## Melakukan sorting dari skor, merapikan dataframe

Dengan melakukan sorting judul anime berdasarkan skor tertinggi, akan memudahkan sistem dalam mencari anime yang memiliki skor tinggi yang cenderung direkomendasikan pada hasil dari rekomendasi sistem.
Setelah dilakukan sorting, saatnya untuk menampilkan anime yang diinginkan, beserta key dalam mencari anime (yaitu anime_id sebagai tolok ukur pencarian anime, dan eng_version merupakan judul dari anime rekomendasi)
"""

df.sort_values(by=['Score'], 
               inplace=True,
               ascending=False,
               na_position='last')

df = df[["anime_id", "eng_version", 
         "Score","Genres","Episodes", 
         "Type", "Premiered", "Members"]]

df

"""## Pengambilan metadata anime dari dataframe (df)

Dari data yang telah dimiliki, maka bila rekomendasi tersebut meminta anime_id tersebut, maka akan diberikan dataframe berdasarkan anime yang dibutuhkan, dan anime yang akan direkomendasikan.
"""

def get_anime_frame(anime):
    if isinstance(anime, int):
        return df[df.anime_id == anime]
    if isinstance(anime, str):
        return df[df.eng_version == anime]

"""## Fungsi eksekusi dari model #1

Berikut adalah fungsi yang akan digunakan dalam menampilkan rekomendasi anime dari judul yang diinputkan untuk model #1.
Dengan memasukkan judul anime yang disukai, maka pengguna bisa mendapatkan rekomendasi dari sistem mengenai anime yang mirip (similiar).
"""

pd.set_option("max_colwidth", None)

def find_similar_animes(name, n=10, return_dist=False, neg=False):
    try:
        index = get_anime_frame(name).anime_id.values[0]
        encoded_index = anime2anime_encoded.get(index)
        weights = anime_weights
        
        dists = np.dot(weights, weights[encoded_index])
        sorted_dists = np.argsort(dists)
        
        n = n + 1
        
        if neg:
            closest = sorted_dists[:n]
        else:
            closest = sorted_dists[-n:]

        print('animes closest to {}'.format(name))

        if return_dist:
            return dists, closest
        
        rindex = df

        SimilarityArr = []

        for close in closest:
            decoded_id = anime_encoded2anime.get(close)
            anime_frame = get_anime_frame(decoded_id)
            
            anime_name = anime_frame.eng_version.values[0]
            genre = anime_frame.Genres.values[0]
            similarity = dists[close]
            SimilarityArr.append({"anime_id": decoded_id, "name": anime_name, "genres":genre,
                                  "similarity": similarity,})

        Frame = pd.DataFrame(SimilarityArr).sort_values(by="similarity", ascending=False)
        return Frame[Frame.anime_id != index].drop(['anime_id'], axis=1)

    except:
        print('{}!, Not Found in Anime list'.format(name))

"""## Fungsi eksekusi dari model #2

Berikut adalah fungsi yang akan digunakan dalam menampilkan rekomendasi anime dari judul yang diinputkan untuk model #2.
Dengan memasukkan judul anime yang disukai, maka pengguna bisa mendapatkan rekomendasi dari sistem mengenai anime yang mirip (similiar).

Fungsi ini hanya disediakan sebagai pembanding, sehingga dapat diketahui model mana yang dapat memberikan rekomendasi dengan lebih baik kepada konsumen.
"""

pd.set_option("max_colwidth", None)

def find_similar_animes_hyper(name, n=10, return_dist=False, neg=False):
    try:
        index = get_anime_frame(name).anime_id.values[0]
        encoded_index = anime2anime_encoded.get(index)
        weights = anime_weights_hyper
        
        dists = np.dot(weights, weights[encoded_index])
        sorted_dists = np.argsort(dists)
        
        n = n + 1
        
        if neg:
            closest = sorted_dists[:n]
        else:
            closest = sorted_dists[-n:]

        print('animes closest to {}'.format(name))

        if return_dist:
            return dists, closest
        
        rindex = df

        SimilarityArr = []

        for close in closest:
            decoded_id = anime_encoded2anime.get(close)
            anime_frame = get_anime_frame(decoded_id)
            
            anime_name = anime_frame.eng_version.values[0]
            genre = anime_frame.Genres.values[0]
            similarity = dists[close]
            SimilarityArr.append({"anime_id": decoded_id, "name": anime_name, "genres":genre,
                                  "similarity": similarity,})

        Frame = pd.DataFrame(SimilarityArr).sort_values(by="similarity", ascending=False)
        return Frame[Frame.anime_id != index].drop(['anime_id'], axis=1)

    except:
        print('{} tidak ditemukan dalam database.'.format(name))

"""## Testing model #1 untuk anime "Naruto" untuk menampilkan 10 anime termirip.

Yap, mari kita lihat hasil pemodelan kita :)
"""

find_similar_animes('Naruto', neg=False)

"""## Testing model #2 untuk anime "Naruto" untuk menampilkan 10 anime termirip.

Yap, mari kita lihat hasil pemodelan kita :)
"""

find_similar_animes_hyper('Naruto', neg=False)

"""# Hasil Dari Rekomendasi:
Dapat dilihat bahwa rekomendasi dari model #1 menunjukkan hasil yang lebih akurat daripada model ke-2, dimana model pertama memberikan hasil yang baik (anime yang direkomendasikan mirip dengan Naruto, baik dari segi cerita, maupun genre).

Sedangkan, pada model ke-2 didapatkan hasil yang kurang memuaskan, dimana anime yang direkomendasikan memiliki tingkat kemiripan yang kurang, bahkan tidak mirip, dari pengujian yang dilakukan.

Secara statistik, rekomendasi dari model pertama juga memberikan hasil berupa MAE, dan MSE yang lebih baik dibandingkan model kedua yang seharusnya merupakan pengembangan darin model pertama. Maka dari itu, dari model tersebut, **akan digunakan model pertama sebagai model yang digunakan dalam proses memberikan rekomendasi anime kepada pengguna.**

# Evaluasi

Dalam proses evaluasi, akan disajikan informasi mengenai perbandingan mengenai model pertama dan kedua melalui tiga metrik berikut:
- Loss (Cross-entropy Loss)
- MAE (Mean Absolute Error)
- MSE (Mean Squared Error)

## Metrik #1: Loss

Metrik loss adalah metrik yang senantiasa digunakan dalam proses pemodelan.
Cross-entropy adalah fungsi loss default yang digunakan untuk masalah klasifikasi biner. Ini dimaksudkan untuk digunakan dengan klasifikasi biner di mana nilai target berada di set {0, 1}.

Secara matematis, ini adalah fungsi loss yang lebih disukai di bawah inference framework of maximum likelihood. Ini adalah fungsi loss yang harus dievaluasi terlebih dahulu dan hanya diubah jika anda memiliki alasan yang bagus.

Cross-entropy akan menghitung skor yang merangkum perbedaan rata-rata antara distribusi probabilitas aktual dan prediksi untuk kelas prediksi 1. Skor tersebut diminimalkan dan nilai cross-entropy yang baik adalah 0.

Berikut adalah hasil perbandingan loss dan val_loss pada kedua model yang telah dibuat dalam grafik:
"""

from matplotlib import pyplot

pyplot.plot(history.history['loss'])
pyplot.plot(history_hyper.history['loss'])
pyplot.show()

from matplotlib import pyplot

pyplot.plot(history.history['val_loss'])
pyplot.plot(history_hyper.history['val_loss'])
pyplot.show()

"""## Metrik #2: MAE

Nilai MAE merepresentasikan rata – rata kesalahan (error) absolut antara hasil peramalan dengan nilai sebenarnya.
Dengan menggunakan nilai yang mudah didapat, namun metrik yang sangat bermanfaat ini, dapat dilihat seberapa besar rata-rata dari kesalahan model dalam melakukan algoritmanya (melakukan prediksi). Semakin kecil nilai dari MAE, maka model berfungsi dengan baik.

MAE sendiri didapatkan dari seluruh prediksi dikurangkan dengan prediksi yang benar, dibagi dengan poin dalam prediksi. Melalui metrik ini, dapat diketahui seberapa besar kemungkinan model dalam melakukan prediksi yang salah.

Pemilihan MAE pada model ini dikarenakan MAE mudah duntuk diterapkan, serta memiliki tujuan yang linier dengan sistem rekomendasi, yaitu mencari kesalahan dari penggunaan model.

Berikut adalah hasil perbandingan MAE pada kedua model yang telah dibuat dalam grafik:
"""

from matplotlib import pyplot

pyplot.plot(history.history['mae'])
pyplot.plot(history_hyper.history['mae'])
pyplot.show()

"""## Metrik #3: MSE

Hampir sama dengan MAE, MSE didapatkan dengan cara masing-masing kesalahan atau sisa dikuadratkan. Kemudian dijumlahkan dan ditambahkan dengan jumlah observasi. Pendekatan ini mengatur kesalahan peramalan yang besar karena kesalahan - kesalahan itu dikuadratkan.
Metode itu menghasilkan kesalahan-kesalahan sedang yang kemungkinan lebih baik untuk kesalahan kecil, tetapi kadang menghasilkan perbedaan yang besar.

Pemilihan metrik ini dalam sistem rekomendasi adalah karena MSE memiliki beberapa keunggulan seperti hasilnya mencakup kesalahan-kesalahan yang lebih besar dari MAE, sehingga dapat diketahui sebesar apa kemungkinan model akan melakukan kesalahan prediksi yang besar.

Berikut adalah hasil perbandingan MSE pada kedua model yang telah dibuat dalam grafik:
"""

pyplot.plot(history.history['mse'])
pyplot.plot(history_hyper.history['mse'])
pyplot.show()

"""# KESIMPULAN

Dari pembuatan kedua model tersebut didapatkan hasil yang cukup optimal, dan sesuai dengan goal yang ingin dicapai, yaitu merekomendasikan beberapa judul anime yang memiliki kemiripan yang tinggi dengan anime yang diinputkan pertama kali.

**Dari proses pemodelan hingga evaluasi, dapat disimpulkan bahwa model #1 yang menggunakan RecommenderNet dan menggunakan optimizer Adam dapat melakukan tugas untuk memberikan rekomendasi anime dengan lebih baik dibandingkan model #2 yang pemodelannya menggunakan SGD optimizer yang dirancang sendiri oleh penulis.**
"""