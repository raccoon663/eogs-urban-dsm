"""Prepare nested geometric subsets, preserving original affine frame/test split."""
import argparse
import json,itertools,hashlib,shutil
from pathlib import Path
import numpy as np
import rasterio
from pyproj import Transformer
parser=argparse.ArgumentParser()
parser.add_argument('--root', type=Path, default=Path('.'))
root=parser.parse_args().root.resolve()
source=root/'data/affine_models/JAX_004'
allmeta=json.loads((source/'affine_models.json').read_text())
train=(source/'train.txt').read_text().splitlines(); test=(source/'test.txt').read_text().splitlines()
key=lambda m:m['img'].replace('.tif','.json')
byid={key(m):m for m in allmeta if m['img']!='Nadir'}
# Dataset loader marks first lexicographic training view as reference. Preserve it.
ids=sorted(train); anchor=0
easting,northing,npix,gsd=np.loadtxt(root/'data/truth/JAX_004/JAX_004_DSM.txt')
gx,gy=np.meshgrid(np.linspace(easting,easting+npix*gsd,33),np.linspace(northing,northing+npix*gsd,33))
directions=[]; quality=[]
for name in ids:
    m=byid[name]; a=np.array(m['model']['coef_']); d=np.cross(a[0],a[1]); d/=np.linalg.norm(d)
    if d[2]<0:d=-d
    directions.append(d)
    cover=[]
    for height in [m['min_alt'],m['max_alt']]:
        xyz=np.stack([gx.ravel(),gy.ravel(),np.full(gx.size,height)],axis=1)
        normalized=(xyz-np.array(m['model']['center']))/m['model']['scale']
        projected=normalized@a.T+np.array(m['model']['intercept_'])
        cover.append(float(np.mean(np.all(np.abs(projected[:,:2])<=1,axis=1))*100))
    with rasterio.open(root/'data/images/JAX_004'/m['img']) as ds:
        im=ds.read(); valid=(ds.dataset_mask()>0)&np.all(np.isfinite(im),axis=0)
        quality.append(dict(id=name,valid_percent=100*valid.mean(),mean=float(im.mean()),std=float(im.std()),date=m.get('acquisition_date'),aoi_coverage_percent_at_min_max_alt=cover))
D=np.degrees(np.arccos(np.clip(np.array(directions)@np.array(directions).T,-1,1)))
def score(comb):
    angles=[D[i,j] for i,j in itertools.combinations(comb,2)]
    return min(angles),sum(angles)
four=max((c for c in itertools.combinations(range(len(ids)),4) if anchor in c),key=score)
eight=max((c for c in itertools.combinations(range(len(ids)),8) if set(four)<=set(c)),key=score)
configs=root/'configs/ablation'; configs.mkdir(parents=True,exist_ok=True)
report={'method':'Exhaustive angular maximin, total pairwise angle tie-break; nested 4 subset of 8 subset of 9; original reference view held fixed. Directions from cross product of affine image-plane rows in normalized UTM.', 'reference_view':ids[anchor], 'image_checks':quality, 'pairwise_angles_deg':D.tolist(),'angle_id_order':ids,'subsets':{}}
for label,comb in [('4',four),('8',eight),('full',tuple(range(len(ids))))]:
    chosen=[ids[i] for i in comb]; target=root/'data/ablation'/label
    target.mkdir(parents=True,exist_ok=True)
    keep=set(chosen+test)
    filtered=[m for m in allmeta if m['img']=='Nadir' or key(m) in keep]
    assert filtered[-1]['img']=='Nadir'
    (target/'affine_models.json').write_text(json.dumps(filtered,indent=2)+'\n')
    # Preserve full-list order, although loader follows metadata order.
    (target/'train.txt').write_text('\n'.join(x for x in train if x in chosen)+'\n')
    shutil.copy2(source/'test.txt',target/'test.txt')
    shutil.copy2(target/'train.txt',configs/f'views_{label}.txt')
    report['subsets'][label]={'views':chosen,'min_angle_deg':score(comb)[0],'sum_angle_deg':score(comb)[1],'affine_sha256':hashlib.sha256((target/'affine_models.json').read_bytes()).hexdigest()}
(configs/'selection.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
