import torch
import argparse

from torch import nn, optim, utils
from torchvision import datasets, transforms
from lib.models.cifar10.FGN import FGN
from lib.helper import ClassifyTrainer, LR_Scheduler

torch.manual_seed(20200504)
torch.cuda.manual_seed(20200504)

parser = argparse.ArgumentParser(description='MNIST')
parser.add_argument('--device', type=str, default='cuda')
parser.add_argument('--lr', type=float, default=0.001)
parser.add_argument('--epoch', type=int, default=200)
parser.add_argument('--batch_size', type=int, default=128)
parser.add_argument('--save_path', type=str, default='./checkpoint/cifar10.pth')

args = parser.parse_args()

# augmentation
train_transformer = transforms.Compose([transforms.Grayscale(3),
                                        transforms.ToTensor(),
                                        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))])

test_transformer = transforms.Compose([transforms.Grayscale(3),
                                       transforms.ToTensor(),
                                       transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))])

# dataset / dataloader
train_dataset = datasets.MNIST(root='../data',
                               train=True,
                               transform=train_transformer,
                               download=True)

train_loader = utils.data.DataLoader(train_dataset,
                                     batch_size=args.batch_size,
                                     shuffle=True)

test_dataset = datasets.MNIST(root='../data',
                              train=False,
                              transform=test_transformer,
                              download=True)

test_loader = utils.data.DataLoader(test_dataset,
                                    batch_size=args.batch_size,
                                    shuffle=True)

# model
print(f"CPU seed : {torch.initial_seed()} GPU seed : {torch.cuda.initial_seed()}")

filters = torch.autograd.Variable(torch.ones(3, 3, 3)).to(args.device)

model = FGN(filters).to(args.device)

# cost
criterion = nn.CrossEntropyLoss().to(args.device)

if args.device == 'cuda':
    criterion = criterion.to(args.device)

train_iter = len(train_loader)
test_iter = len(test_loader)

# optimizer/scheduler
optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=0.9, weight_decay=1e-5)
scheduler = LR_Scheduler(mode='poly',
                         base_lr=args.lr,
                         num_epochs=args.epoch,
                         iters_per_epoch=train_iter)

trainer = ClassifyTrainer(model,
                          train_loader,
                          test_loader,
                          criterion,
                          optimizer,
                          scheduler = scheduler)

best_test_acc = 0

# train
for e in range(args.epoch):
    train_loss, train_acc = trainer.train(epoch = e)
    test_loss, test_acc = trainer.test()

    train_acc = train_acc / args.batch_size
    test_acc = test_acc / args.batch_size

    if test_acc > best_test_acc:
        trainer.save(args.save_path)
        best_test_acc = test_acc

    print(f"Epoch [ {args.epoch} / {e} ] \n"
          f" + TRAIN [Loss / Acc] : [ {train_loss} / {train_acc} ] \n"
          f" + TEST  [Loss / Acc] : [ {test_loss} / {test_acc} ]")