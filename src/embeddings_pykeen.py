from pykeen.triples import TriplesFactory
from pykeen.pipeline import pipeline
import pickle
import os

data_path  = r"..\data\CSV\relations_for_pykeen.csv"
output_folder = r'pykeen\RGCN_dim100_epoch1'

tf = TriplesFactory.from_path(data_path, create_inverse_triples = True)
training, testing = tf.split([.999, .001])

for (data, name) in zip(
[training.relation_to_id, training.entity_to_id, testing.relation_to_id, testing.entity_to_id],
["train_relations.pickle", "train_nodes.pickle", "test_relations.pickle", "test_relations.pickle"]):
    outputfile = open(os.path.join(output_folder, name),'wb')
    pickle.dump(data,outputfile)
    outputfile.close()



result = pipeline(
    training=training,
    testing=testing,
    model='RGCN',
    model_kwargs=dict(interaction = 'distmult', preferred_device ="cuda", embedding_dim = 100),
    training_kwargs=dict(num_epochs=1)
)

result.save_to_directory(output_folder)
