python3 ged2dot.py --familydepth 999 --rootfamily F500001 --input   ../tree_2024_gedcom.ged \
    > tree_2024_gedcom.gv

# dot -Tsvg -otree_2024_gedcom.svg tree_2024_gedcom.gv

sed s/shape=box,// tree_2024_gedcom.gv > jnk$$
mv jnk$$ tree_2024_gedcom.gv
sed 's/splines = ortho;/& node [style="rounded,filled" shape=box]/' tree_2024_gedcom.gv > jnk$$
mv jnk$$ tree_2024_gedcom.gv
open  tree_2024_gedcom.gv

dot -Tsvg -otree_2024_gedcom.svg tree_2024_gedcom.gv
open tree_2024_gedcom.svg
