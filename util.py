import os, shutil
import ollama

def clearFolder(path):
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def getAvailiableModels():
    models = ollama.list()['models']

    model_names = []
    for model in models:
        model_names.append(model['name'])
    return model_names