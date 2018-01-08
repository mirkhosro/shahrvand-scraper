library(tidyverse)

## TOD: read multiple files (from a folder?) and remove rows with duplicated ids
prods <- read_csv("../data/foods.csv")
brand_map <- read_csv("../data/brand_map_full.csv")
supraano_cat <- read_csv("../data/supraano_db_categories.csv") %>% filter(status == 1)

## clean up columns
prods <- prods %>% rename("name" = "title", "tag" = "keywords",
            "price" = "orig_price", "image" = "image_file") %>%
            add_column(status = 0)
## keep only products that have a price
prods <- prods %>% filter(!is.na(price))
## make a size column from weight or volumn columns
make_size <- function(wgt, vol) {
  paste0(
    ifelse(is.na(wgt), "", paste0("Wgt:", wgt, " g")),
    ifelse(is.na(vol), "", paste0("Vol:", vol, " ml"))
  )
}
prods <- prods %>% mutate(size = make_size(weight_g, volume_ml))
## add Supraano brand_id from the mapping
prods$brand_id <- left_join(prods["brand"], brand_map, by = c("brand" = "shahrvand_brand"))$id
categ <- left_join(prods, supraano_cat[c("id", "name")],
                               by = c("sub_categ" = "name"))
null_id <- categ[is.na(categ$id), ]# %>% select(sub_categ) %>% unique
any(is.na(categ$id))
prods$category_id <- categ$id
prods <- prods %>% select(-c(raw_title, brand, current_price, weight_g, volume_ml, categ, sub_categ))
this_time = as.character(lubridate::now())
prods$created_at <- this_time
prods$updated_at <- this_time
prods$image <- paste0("http://supraano.com/storage/Product/sh_", prods$shahrvand_id, ".jpg")

write_csv(prods, path = "../data/foods_ready_for_db.csv")

## TODO: insert code that updates the database directly here
library(RMariaDB)
