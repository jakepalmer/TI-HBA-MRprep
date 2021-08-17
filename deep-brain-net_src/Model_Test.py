import sys
from keras.models import load_model
import pandas as pd
import numpy as np
from keras.preprocessing.image import ImageDataGenerator

test_dir = sys.argv[1]
out_file = sys.argv[2]
model_file = sys.argv[3]
subject = sys.argv[4]

model = load_model(model_file)

batch_size = 80

datagen_test = ImageDataGenerator(rescale=1./255, horizontal_flip=False, vertical_flip=False,
                                  featurewise_center=False, featurewise_std_normalization=False)


test_generator = datagen_test.flow_from_directory(
    directory=str(test_dir),
    batch_size=batch_size,
    seed=42,
    shuffle=False,
    class_mode=None)


labels_test = []
sitelist = []
IDlist = []
sex_test = []
slice_test = []
deplist = []
test_generator.reset()
i = 0


for x in test_generator.filenames:
    i = i+1
    sl = x.split('-')[1].split('.')[0]
    x = x.split('_T1')[0]
    IDlist.append(x)


test_generator.reset()
predicty = model.predict_generator(
    test_generator, verbose=0, steps=test_generator.n/batch_size)


prediction_data = pd.DataFrame()
prediction_data['ID'] = IDlist

prediction_data['Prediction'] = predicty

IDset = set(prediction_data['ID'].values)
IDset = list(IDset)

final_prediction = []

for x in IDset:
    check_predictions = prediction_data[prediction_data['ID']
                                        == x]['Prediction']
    predicty = check_predictions.reset_index(drop=True)
    final_prediction.append(predicty)

predicty1 = np.median(final_prediction)
out_data = pd.DataFrame({'ID': [subject], 'Pred_Age': [predicty1]})
out_data.to_csv(out_file, index=False)
