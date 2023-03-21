# -*- coding: utf-8 -*-
"""Christian_Altrichter_Ass4_helper_code_2022.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1USTkHCKr8sjwyowycrnv4XITAdkPwiWA
"""

import os
import math
import time
from tqdm import tqdm

import torch
import torch.nn as nn
from torch.utils.data import Dataset
from torch.utils.data import DataLoader

DEVICE = 'cuda'

from google.colab import drive
drive.mount('/content/drive')

# ______________________________________________________________________________
# QUESTION 1.1.

# Returns tuple of (number of lines, number of characters) 
def number_sent_chars(file):
  f = open(file, 'r')
  text = f.read()

  # Get number of characters
  stripped = text.replace("\n",'')
  num_char = len(stripped) 

  sentenceArray = text.split('\n')

  counter = 0
  for linie in sentenceArray:
    counter += 1

  # CAREFUL, last line empty
  counter -= 1
  
  f.close()
  return counter, num_char
  

# Returns as touple the average lengths (by characters) for questions then answers
def avg_length(questions):
  f = open(questions, 'r')
  text = f.read()

  # Get number of characters
  stripped = text.replace("\n",'')
  num_char = len(stripped) 

  sentenceArray = text.split('\n')

  counter = 0
  for linie in sentenceArray:
    counter += 1

  # CAREFUL, last line empty
  counter -= 1

  avglen1 = num_char / counter

  f.close()
  return avglen1 

train1 = '/content/drive/MyDrive/DLL_Ass_4/numbers__place_value/train.x'
valid1 = '/content/drive/MyDrive/DLL_Ass_4/numbers__place_value/train.y'
train2 = '/content/drive/MyDrive/DLL_Ass_4/numbers__place_value/interpolate.x'
valid2 = '/content/drive/MyDrive/DLL_Ass_4/numbers__place_value/interpolate.y'


print(number_sent_chars(train1))
print(number_sent_chars(valid1))
print(number_sent_chars(train2))
print(number_sent_chars(valid2))

print(avg_length(train1))
print(avg_length(valid1))
print(avg_length(train2))
print(avg_length(valid2))

class Vocabulary:

    def __init__(self, pad_token="<pad>", unk_token='<unk>', eos_token='<eos>', sos_token='<sos>'):
        self.id_to_string = {}
        self.string_to_id = {}
        
        # add the default pad token
        self.id_to_string[0] = pad_token
        self.string_to_id[pad_token] = 0
        
        # add the default unknown token
        self.id_to_string[1] = unk_token
        self.string_to_id[unk_token] = 1
        
        # add the default unknown token
        self.id_to_string[2] = eos_token
        self.string_to_id[eos_token] = 2   

        # add the default unknown token
        self.id_to_string[3] = sos_token
        self.string_to_id[sos_token] = 3

        # shortcut access
        self.pad_id = 0
        self.unk_id = 1
        self.eos_id = 2
        self.sos_id = 3

    def __len__(self):
        return len(self.id_to_string)

    def add_new_word(self, string):
        self.string_to_id[string] = len(self.string_to_id)
        self.id_to_string[len(self.id_to_string)] = string

    # Given a string, return ID
    # if extend_vocab is True, add the new word
    def get_idx(self, string, extend_vocab=False):
        if string in self.string_to_id:
            return self.string_to_id[string]
        elif extend_vocab:  # add the new word
            self.add_new_word(string)
            return self.string_to_id[string]
        else:
            return self.unk_id


# Read the raw txt file and generate a 1D pytorch tensor
# containing the whole text mapped to sequence of token ID,
# and a vocab file
class ParallelTextDataset(Dataset):

    def __init__(self, src_file_path, trg_file_path, src_vocab=None,
                 trg_vocab=None, extend_vocab=False, device='cuda'):
        (self.data, self.src_vocab, self.trg_vocab,
         self.src_max_seq_length, self.tgt_max_seq_length) = self.parallel_text_to_data(
            src_file_path, trg_file_path, src_vocab, trg_vocab, extend_vocab, device)

    def __getitem__(self, idx):
        return self.data[idx]

    def __len__(self):
        return len(self.data)

    def parallel_text_to_data(self, src_file, tgt_file, src_vocab=None, tgt_vocab=None,
                          extend_vocab=False, device='cuda'):
        # Convert paired src/tgt texts into torch.tensor data.
        # All sequences are padded to the length of the longest sequence
        # of the respective file.

        assert os.path.exists(src_file)
        assert os.path.exists(tgt_file)

        if src_vocab is None:
            src_vocab = Vocabulary()

        if tgt_vocab is None:
            tgt_vocab = Vocabulary()
        
        data_list = []
        # Check the max length, if needed construct vocab file.
        src_max = 0
        with open(src_file, 'r') as text:
            for line in text:
                tokens = list(line)
                length = len(tokens)
                if src_max < length:
                    src_max = length

        tgt_max = 0
        with open(tgt_file, 'r') as text:
            for line in text:
                tokens = list(line)
                length = len(tokens)
                if tgt_max < length:
                    tgt_max = length
        tgt_max += 2  # add for begin/end tokens
                    
        src_pad_idx = src_vocab.pad_id
        tgt_pad_idx = tgt_vocab.pad_id

        tgt_eos_idx = tgt_vocab.eos_id
        tgt_sos_idx = tgt_vocab.sos_id

        # Construct data
        src_list = []
        print(f"Loading source file from: {src_file}")
        with open(src_file, 'r') as text:
            for line in tqdm(text):
                seq = []
                tokens = list(line)
                for token in tokens:
                    seq.append(src_vocab.get_idx(token, extend_vocab=extend_vocab))
                var_len = len(seq)
                var_seq = torch.tensor(seq, device=device, dtype=torch.int64)
                # padding
                new_seq = var_seq.data.new(src_max).fill_(src_pad_idx)
                new_seq[:var_len] = var_seq
                src_list.append(new_seq)

        tgt_list = []
        print(f"Loading target file from: {tgt_file}")
        with open(tgt_file, 'r') as text:
            for line in tqdm(text):
                seq = []
                tokens = list(line)
                # append a start token
                seq.append(tgt_sos_idx)
                for token in tokens:
                    seq.append(tgt_vocab.get_idx(token, extend_vocab=extend_vocab))
                # append an end token
                seq.append(tgt_eos_idx)

                var_len = len(seq)
                var_seq = torch.tensor(seq, device=device, dtype=torch.int64)

                # padding
                new_seq = var_seq.data.new(tgt_max).fill_(tgt_pad_idx)
                new_seq[:var_len] = var_seq
                tgt_list.append(new_seq)

        # src_file and tgt_file are assumed to be aligned.
        assert len(src_list) == len(tgt_list)
        for i in range(len(src_list)):
            data_list.append((src_list[i], tgt_list[i]))

        print("Done.")
            
        return data_list, src_vocab, tgt_vocab, src_max, tgt_max

# `DATASET_DIR` should be modified to the directory where you downloaded the dataset.
DATASET_DIR = "/content/drive/MyDrive/DLL_Ass_4"

TRAIN_FILE_NAME = "train"
VALID_FILE_NAME = "interpolate"

INPUTS_FILE_ENDING = ".x"
TARGETS_FILE_ENDING = ".y"

# TASK = "numbers__place_value"
# TASK = "comparison__sort"
TASK = "algebra__linear_1d"

# Adapt the paths!

src_file_path = f"{DATASET_DIR}/{TASK}/{TRAIN_FILE_NAME}{INPUTS_FILE_ENDING}"
trg_file_path = f"{DATASET_DIR}/{TASK}/{TRAIN_FILE_NAME}{TARGETS_FILE_ENDING}"

train_set = ParallelTextDataset(src_file_path, trg_file_path, extend_vocab=True)

# get the vocab
src_vocab = train_set.src_vocab
trg_vocab = train_set.trg_vocab

src_file_path = f"{DATASET_DIR}/{TASK}/{VALID_FILE_NAME}{INPUTS_FILE_ENDING}"
trg_file_path = f"{DATASET_DIR}/{TASK}/{VALID_FILE_NAME}{TARGETS_FILE_ENDING}"

valid_set = ParallelTextDataset(
    src_file_path, trg_file_path, src_vocab=src_vocab, trg_vocab=trg_vocab,
    extend_vocab=False)

batch_size = 64

train_data_loader = DataLoader(
    dataset=train_set, batch_size=batch_size, shuffle=True)

valid_data_loader = DataLoader(
    dataset=valid_set, batch_size=batch_size, shuffle=False)

src_vocab.id_to_string

trg_vocab.id_to_string

########
# Taken from:
# https://pytorch.org/tutorials/beginner/transformer_tutorial.html
# or also here:
# https://github.com/pytorch/examples/blob/master/word_language_model/model.py
class PositionalEncoding(nn.Module):

    def __init__(self, d_model, dropout=0.0, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        self.max_len = max_len

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float()
                             * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)  # shape (max_len, 1, dim)
        self.register_buffer('pe', pe)  # Will not be trained.

    def forward(self, x):
        """Inputs of forward function
        Args:
            x: the sequence fed to the positional encoder model (required).
        Shape:
            x: [sequence length, batch size, embed dim]
            output: [sequence length, batch size, embed dim]
        """
        assert x.size(0) < self.max_len, (
            f"Too long sequence length: increase `max_len` of pos encoding")
        # shape of x (len, B, dim)
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)

# The model has been changed in a final step to solve question 7.3
class TransformerModel(nn.Module):

    # For all regular training  
    # def __init__(self, source_vocabulary_size, target_vocabulary_size,
    #              d_model=256, pad_id=0, encoder_layers=3, decoder_layers=2,
    #              dim_feedforward=1024, num_heads=8):
    
    # For 7.5 increased complexity expression, using almost default values. 
    def __init__(self, source_vocabulary_size, target_vocabulary_size,
                 d_model=512, pad_id=0, encoder_layers=6, decoder_layers=6,
                 dim_feedforward=2048, num_heads=8):
    
    # For 7.3 reduced dim_feedforward, encoder_layers and decoder_layers
    # def __init__(self, source_vocabulary_size, target_vocabulary_size,
    #              d_model=256, pad_id=0, encoder_layers=1, decoder_layers=1,
    #              dim_feedforward=1024, num_heads=8):
      
        # all arguments are (int)
        super().__init__()
        self.pad_id = pad_id

        self.embedding_src = nn.Embedding(
            source_vocabulary_size, d_model, padding_idx=pad_id)
        self.embedding_tgt = nn.Embedding(
            target_vocabulary_size, d_model, padding_idx=pad_id)

        self.pos_encoder = PositionalEncoding(d_model)
        self.transformer = nn.Transformer(
            d_model, num_heads, encoder_layers, decoder_layers, dim_feedforward)
        self.encoder = self.transformer.encoder
        self.decoder = self.transformer.decoder
        self.linear = nn.Linear(d_model, target_vocabulary_size)

    def create_src_padding_mask(self, src):
        # input src of shape ()
        # print(src)
        src_padding_mask = src.transpose(0, 1) == 0
        return src_padding_mask

    def create_tgt_padding_mask(self, tgt):
        # input tgt of shape ()
        tgt_padding_mask = tgt.transpose(0, 1) == 0
        return tgt_padding_mask

# ______________________________________________________________________________
# QUESTION 4
# Source: This source has helped me to develop a greedy decoder 
# https://kikaben.com/transformers-evaluation-details/

    def greedy_search(self, src, tgt):

      # tokenize our input as list
      input_tokens = src.id_to_string

      # Then we convert input_tokens as an input tensor to the encoder
      token_list = []
      for elem in input_tokens:
        token_list.append(elem)
      
      encoder_input = torch.tensor([input_tokens])

      # Generate encoded features
      self.eval()
      with torch.no_grad(): 
        encoder_output = self.encoder(encoder_input)

      # Start with SOS token ID, for us 3
      decoder_input = torch.Tensor([[3]]).long()

      # define maximum output length (+50 random)
      max_output_length = encoder_input.shape[-1] + 50

      # Autoregressiv:
      for i in range(max_output_length):

        # Decoder predictions
        logits = self.decoder(encoder_output, decoder_input)

        # greedy selection
        token_idx = torch.argmax(logits[: -1], keepdim = True)

        # If the EOS is now the most probable, we terminate
        if token_idx.item()==self.eos_id:
          break
        
        # Next input for the decoder
        decoder_input = torch.cat([decoder_input, token_idx], dim=1)

        # len because <sos>, token, <eos> 
        if len(decoder_input[0]) == 3:
          break
      
      # Decoder input is a batch of one entry, and we also exlude SOS 
      decoder_output = decoder_input[0,1:].numpy()

      # Convert token indices to token texts 
      output_texts = [self.id_to_string[i] for i in decoder_output]

      return output_texts


    def forward(self, src, tgt):
        """Forward function.

        Parameters:
          src: tensor of shape (sequence_length, batch, data dim)
          tgt: tensor of shape (sequence_length, batch, data dim)
        Returns:
          tensor of shape (sequence_length, batch, data dim)
        """
        # print("now in forward")
        # print("Src is:", src)
        # print("Trg is:", tgt)
        
        src_key_padding_mask = self.create_src_padding_mask(src).to(DEVICE)
        # print("src after key padding mask", src_key_padding_mask.shape)
        tgt_key_padding_mask = self.create_tgt_padding_mask(tgt).to(DEVICE)
        # print("tgt after key padding mask", tgt_key_padding_mask.shape)
        memory_key_padding_mask = src_key_padding_mask
        # print("src after key memo padding mask", tgt_key_padding_mask.shape)
        tgt_mask = self.transformer.generate_square_subsequent_mask(
            tgt.shape[0]).to(DEVICE)
        # print("tgt after key square padding mask", tgt_key_padding_mask.shape)

        tgt = self.embedding_tgt(tgt)
        # print("tgt after embedding", tgt.shape)
        tgt = self.pos_encoder(tgt)
        # print("tgt after encoding", tgt.shape)
        out = self.embedding_src(src)
        # print("src after embedding", out.shape)
        out = self.pos_encoder(out)
        # print("src after encoder", out.shape)
        out = self.transformer(
            out, tgt, src_key_padding_mask=src_key_padding_mask,
            tgt_mask=tgt_mask, tgt_key_padding_mask=tgt_key_padding_mask,
            memory_key_padding_mask=memory_key_padding_mask)
        out = self.linear(out)
        return out

# ______________________________________________________________________________
# QUESTION 3.1
# Source to help implement forward_seperate() was https://pytorch.org/docs/stable/generated/torch.nn.Transformer.html

    def forward_seperate(self, src, tgt):
        """Forward function.

        Parameters:
          src: tensor of shape (sequence_length, batch, data dim)
          tgt: tensor of shape (sequence_length, batch, data dim)
        Returns:
          tensor of shape (sequence_length, batch, data dim)
        """
        src_key_padding_mask = self.create_src_padding_mask(src).to(DEVICE)
        tgt_key_padding_mask = self.create_tgt_padding_mask(tgt).to(DEVICE)
        memory_key_padding_mask = src_key_padding_mask
        tgt_mask = nn.Transformer.generate_square_subsequent_mask(
            tgt.shape[0]).to(DEVICE)

        tgt = self.embedding_tgt(tgt)
        tgt = self.pos_encoder(tgt)
        out = self.embedding_src(src)
        out = self.pos_encoder(out)
        memory = self.encoder(out, src_key_padding_mask=src_key_padding_mask)
        out = self.decoder(tgt, memory, tgt_mask=tgt_mask,
                              tgt_key_padding_mask=tgt_key_padding_mask,
                              memory_key_padding_mask=memory_key_padding_mask)

        out = self.linear(out)
        return out

"""Training"""

import numpy as np

# ______________________________________________________________________________
# QUESTION 5

def cal_accuracy(out, tgt, result_array):
    predicted = out.argmax(dim=-1).cpu().detach()

    # for forward remove the leading character!
    target = tgt[1:].cpu().detach()
    
    # local_acc_count = 0

    torch.set_printoptions(threshold=10_000)

    # for i in range(len(predicted[0])):
    #   counter = 0
    #   for j in range(len(predicted)):
    #     # print("i is", i, "and j is ", j)
    #     # print("tgt in loop is:", target[i][j])
    #     # print("predicted in loop is:", predicted[i][j])
    #     if target[j][i] == 0:
    #       counter += 1
    #     elif target[j][i] == predicted[j][i]:
    #       counter += 1
    #   if counter == len(predicted):
    #     local_acc_count += 1

    # Code below replaced by above to improve performance
    transform1 = ((target == 0) | (target == predicted))
    transform2 = transform1.all(dim = 0)
    transform3 = transform2.sum() / transform2.shape[0]

    
    # acc = local_acc_count / len(predicted)
    result_array.append(transform3.numpy())

def remove_eos(tgt):
  forward_target = tgt.clone()

  # for i in range(len(tgt[0])):
  #   for j in range(len(tgt)):
  #     if tgt[j][i] == 2:
  #       forward_target[j][i] = 0
  #     else:
  #       forward_target[j][i] = tgt[j][i]

  # Code below replaced by above to improve performance
  forward_target[forward_target == 2] = 0 

  # print(target)
  
  return forward_target

# ______________________________________________________________________________
# QUESTION 6

model = TransformerModel(len(src_vocab), len(trg_vocab))
model = model.to(DEVICE)
loss_fn = nn.CrossEntropyLoss(ignore_index=0)
learning_rate = 0.0001
clipping_rate = 0.1
optimizer = torch.optim.Adam(params=model.parameters(), lr = learning_rate)

model.train()
log_interval = 10

t_losses = []
v_losses = []

t_accuracy = []
v_accuracy = []

# ______________________________________________________________________________
# QUESTION 7.5 restoration
model = TransformerModel(len(src_vocab), len(trg_vocab))
model = model.to(DEVICE)
model.load_state_dict(torch.load("/content/drive/MyDrive/StateSave/850Model_linear.pt"))
# print(dir(model))

loss_fn = nn.CrossEntropyLoss(ignore_index=0)
learning_rate = 0.0001
clipping_rate = 0.1
optimizer = torch.optim.Adam(params=model.parameters(), lr = learning_rate)
optimizer.load_state_dict(torch.load("/content/drive/MyDrive/StateSave/850Optimizer.pt"))

model.train()
log_interval = 10

t_losses =  list(np.load("/content/drive/MyDrive/StateSave/850t_loss.npy"))
v_losses = list(np.load("/content/drive/MyDrive/StateSave/850v_loss.npy"))

t_accuracy = list(np.load("/content/drive/MyDrive/StateSave/850t_accuracy.npy"))
v_accuracy = list(np.load("/content/drive/MyDrive/StateSave/850v_accuracy.npy"))

def save_state():
  torch.save(model.state_dict(), "/content/drive/MyDrive/Model_linear.pt")
  torch.save(optimizer.state_dict(), "/content/drive/MyDrive/Optimizer.pt")

  np.save("/content/drive/MyDrive/t_accuracy", np.array(t_accuracy))
  np.save("/content/drive/MyDrive/v_accuracy", np.array(v_accuracy))
  np.save("/content/drive/MyDrive/t_loss", np.array(t_losses))
  np.save("/content/drive/MyDrive/v_loss", np.array(v_losses))

  print("---------------------- state save completed ----------------------")

# adapt paths if necessary
def load_state():
  model = TransformerModel(len(src_vocab), len(trg_vocab))
  model = model.to(DEVICE)
  model.load_state_dict(torch.load("/content/drive/MyDrive/Model_linear.pt"))
  # print(dir(model))

  loss_fn = nn.CrossEntropyLoss(ignore_index=0)
  learning_rate = 0.0001
  clipping_rate = 0.1
  optimizer = torch.optim.Adam(params=model.parameters(), lr = learning_rate)
  optimizer.load_state_dict(torch.load("/content/drive/MyDrive/Model_linear.pt"))

  t_losses =  list(np.load("/content/drive/MyDrive/t_loss.npy"))
  v_losses = list(np.load("/content/drive/MyDrive/v_loss.npy"))

  t_accuracy = list(np.load("/content/drive/MyDrive/t_accuracy.npy"))
  v_accuracy = list(np.load("/content/drive/MyDrive/v_accuracy.npy"))

in_training = True

while(in_training):

  train_loss = 0

  for i, data in enumerate(train_data_loader):

    model.train()

    if i % 100 == 0:
      print("batch i is", i)

    source = torch.transpose(data[0],0, 1).to(DEVICE)

    target = torch.transpose(data[1],0, 1).to(DEVICE)

    forward_target = remove_eos(target)

    #take everything but the token for forward pass
    output = model(source, forward_target[:-1])

    # Training accuracy
    cal_accuracy(output, target, t_accuracy)

    output = output.transpose(1,2)

    target = target[1:]

    loss = loss_fn(output, target)

    train_loss += loss.item()

    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), clipping_rate)

    if i % log_interval == 0:
        optimizer.step()
        optimizer.zero_grad()
    
    if i == 0:
      t_losses.append(train_loss)
      train_loss = 0
    elif i % 100 == 0:
      t_losses.append(train_loss / 100)
      train_loss = 0
    
    if i % 32000 == 0:
      save_state()
    
    # for regular training every 100
    # if i % 100 == 0:
    # for 7.5 only every 1000 to improve efficiency
    if i % 1000 == 0:
      with torch.no_grad():
          model.eval()
          # print("now in validation")
          loss_fn = nn.CrossEntropyLoss()
          val_loss = 0
          for j, batch in enumerate(valid_data_loader):
              source = torch.transpose(batch[0],0, 1).to(DEVICE)
              target = torch.transpose(batch[1],0, 1).to(DEVICE)

              forward_target = remove_eos(target)
      
              # print("forward target", forward_target)

              output = model(source, forward_target[:-1]) 

              # print("output", output)

              # Validation accuracy 
              cal_accuracy(output, target, v_accuracy)

              # output = output.view(-1, output.shape[-1])
              output = output.transpose(1,2)

              # target = target[1:].reshape(-1)
              target = target[1:]

              loss = loss_fn(output, target)

              val_loss += loss.item()
              
              if j == 0:
                v_losses.append(val_loss)
                val_loss = 0
              elif j % 100 == 0:
                v_losses.append(val_loss / 100)
                val_loss = 0


      print("valid losses", v_losses[-1])
      print("train loss ev is", t_losses[-1])
      t_mean = t_accuracy[-100:]
      print("T accuracy is ", np.mean(t_mean))
      v_mean = v_accuracy[-100:]
      print("V accuracy is ", np.mean(v_mean))

      # For number place & comparison sort
      if (v_accuracy[-1] >= 0.9):
        print("training finished")
        in_training = False
        break

      # For 7.5 
      # if (v_accuracy[-1] >= 0.85):
      #   print("training finished")
      #   in_training = False
      #   break

# ______________________________________________________________________________
# Plooting for the entirety of Question 7

import matplotlib.pyplot as plt

def plot_loss_and_acc(val_acc, val_loss, train_acc, train_loss):
  # Adjustment for training data
  step = len(train_loss) // 100
  step_acc_train = len(train_acc) // 100
  run_loss = train_loss[0]
  run_acc = train_acc[0]
  out_loss_train = []
  out_acc_train = []

  # Loss
  counter = 0
  for i in range(1,len(train_loss)):
    if i == 0:
      continue
    if i % step == 0:
      out_loss_train.append(run_loss / step)
      run_loss = 0
      counter = 0

    counter += 1

    run_loss += train_loss[i]

  if counter != 0:
    out_loss_train.append(run_loss / counter) 
  print(len(out_loss_train))

  # Accuracy
  counter = 0
  for i in range(1, len(train_acc)):
    if i == 0:
      continue
    if i % step_acc_train == 0:
      out_acc_train.append(run_acc / step_acc_train)
      run_acc = 0
      counter = 0
    
    counter += 1

    run_acc +=  train_acc[i]

  if counter != 0:
    out_acc_train.append(run_acc / counter)

  print(len(out_acc_train))

  # Adjustment for validation data
  step_val = len(val_loss) // 100
  step_acc_val = len(val_acc) // 100
  run_loss_val = val_loss[0]
  run_acc_val = val_acc[0]
  out_loss_val = []
  out_acc_val = []

  # Loss
  counter = 0
  for i in range(1,len(val_loss)):
    if i == 0:
      continue
    if i % step_val == 0:
      out_loss_val.append(run_loss_val / step_val)
      run_loss_val = 0
      counter = 0

    counter += 1
    run_loss_val += val_loss[i]

  print("vall loss original is", len(val_loss))

  if counter != 0:
    out_loss_val.append(run_loss_val / counter)

  # Accuracy
  counter = 0
  for i in range(1, len(val_acc)):
    if i == 0:
      continue
    if i % step_acc_val == 0:
      out_acc_val.append(run_acc_val / step_acc_val)
      run_acc_val = 0
      counter = 0

    counter += 1

    run_acc_val +=  val_acc[i]

  if counter != 0:
    out_acc_val.append(run_acc_val / counter)

  # Loss evolution val
  fig, loss = plt.subplots()
  loss.plot(range(0, len(out_loss_val)),out_loss_val,"-")
  loss.set_xlabel("Iteration count (divided by 100)", fontsize = 16)
  loss.set_ylabel("Loss", fontsize = 16)
  loss.set_title(f"Loss validation")
  plt.show()

  # Loss evolution train
  fig, loss2 = plt.subplots()
  loss2.plot(range(0,len(out_loss_train)), out_loss_train, "-")
  loss2.set_xlabel("Iteration count (divided by 100)", fontsize = 16)
  loss2.set_ylabel("Loss", fontsize = 16)
  loss2.set_title(f"Loss training")
  plt.show()

  # accuracy evolution val
  fig, acc = plt.subplots()
  acc.plot(range(0, len(out_acc_val)),out_acc_val,"-")
  acc.set_xlabel("Iteration count (divided by 100)", fontsize = 16)
  acc.set_ylabel("Accuracy", fontsize = 16)
  acc.set_title(f"Accuracy validation")
  acc.set_ylim([0, 1])
  plt.show()

  # # accuracy evolution train
  fig, acc2 = plt.subplots()
  acc2.plot(range(0,len(out_acc_train)), out_acc_train, "-")
  acc2.set_xlabel("Iteration count (divided by 100)", fontsize = 16)
  acc2.set_ylabel("Accuracy", fontsize = 16)
  acc2.set_title(f"Accuracy training")
  acc2.set_ylim([0, 1])
  plt.show()

plot_loss_and_acc(v_accuracy, v_losses, t_accuracy, t_losses)

# ______________________________________________________________________________
# QUESTION 7.2

count = 0

for j, batch in enumerate(valid_data_loader):
    source = torch.transpose(batch[0],0, 1)
    target = torch.transpose(batch[1],0, 1)
    break

# print(source.shape)
# print(target.shape)

m = model(source, target[:-1]).cpu().detach().argmax(dim = -1)

print(m.shape)

def translation(x, dict):
  out = ""
  for i in x:
    out += dict.id_to_string[int(i)]
  return out

for i in range(30,33):
  print("Question ", 1, ":",translation(source[:,i], src_vocab))
  print("Answer ", 2, ":", translation(target[1:,i], trg_vocab))
  print("Prediction", 3, " :", translation(m[:,i], trg_vocab))