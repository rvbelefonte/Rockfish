

addpath('~/sw/SegyMAT')


isegy = '/Users/ncm/Rockfish/rockfish/tests/data/pos_neg.segy';

[D,TH,SH]=ReadSegy(isegy);

i=1;
fprintf('TH(%i).SourceX: %f\n',i,TH(i).SourceX)
fprintf('TH(%i).SourceY: %f\n',i,TH(i).SourceY)
fprintf('TH(%i).GroupX: %f\n',i,TH(i).GroupX)
fprintf('TH(%i).GroupY: %f\n',i,TH(i).GroupY)
