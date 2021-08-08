from pykeen.triples import TriplesFactory
from pykeen.pipeline import pipeline
import argparse
import pickle
import os

data_path  = r"..\data\CSV\relations_for_pykeen_final.csv"


parser = argparse.ArgumentParser(description='')
parser.add_argument("-d", "--dim", type=int, help="Embedding dimension", required=True)
parser.add_argument("-e", "--epochs", type=int, help="Number of epochs to train", required=True)
parser.add_argument("-a", "--algo", type=str, help="algorithm", required=True)

args = parser.parse_args()

dim = args.dim
algo = args.algo
epochs = args.epochs

print("Algorithm: {0}\nEmbedding dimensions: {1}\nEpochs: {2}".format(algo, dim, epochs))

output_folder = r'pykeen\{0}_dim{1}_epoch{2}'.format(algo, dim, epochs)

# Create output folder if it does not exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

tf = TriplesFactory.from_path(data_path, create_inverse_triples = True)
training, testing = tf.split([.999, .001])

# Store all node information so we do not lose track of their names
for (data, name) in zip(
[training.relation_to_id, training.entity_to_id, testing.relation_to_id, testing.entity_to_id],
["train_relations.pickle", "train_nodes.pickle", "test_relations.pickle", "test_nodes.pickle"]):
    outputfile = open(os.path.join(output_folder, name),'wb')
    pickle.dump(data,outputfile)
    outputfile.close()


# Train model and save it
if algo == "RGCN":
    result = pipeline(
        training=training,
        testing=testing,
        model='RGCN',
        model_kwargs=dict(interaction = 'distmult', preferred_device ="cuda", embedding_dim = dim),
        training_kwargs=dict(num_epochs=epochs)
    )
elif algo == "TransE":
    result = pipeline(
        training=training,
        testing=testing,
        model='TransE',
        model_kwargs=dict(preferred_device ="cuda", embedding_dim = dim),
        training_kwargs=dict(num_epochs=epochs)
    )
elif algo == "TuckER":
    result = pipeline(
        training=training,
        testing=testing,
        model='TuckER',
        model_kwargs=dict(preferred_device ="cuda", embedding_dim = dim),
        training_kwargs=dict(num_epochs=epochs, checkpoint_name='tucker_checkpoint.pt',)
    )
result.save_to_directory(output_folder)
