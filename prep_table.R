library(tidyverse)

## TOD: read multiple files (from a folder?) and remove rows with duplicated ids
prods <- read_csv("../data/toiletry1.csv")
brand_map <- read_csv("../data/brand_map_full.csv")
supraano_cat <- read_csv("../data/supraano_db_categories.csv")

## clean up columns
foods <- foods %>% rename("name" = "title", "tag" = "keywords",
            "price" = "orig_price", "image" = "image_file") %>%
            add_column(status = 0)


## make a size column from weight or volumn columns
make_size <- function(wgt, vol) {
  paste0(
    ifelse(is.na(wgt), "", paste0("Wgt:", wgt, " g")),
    ifelse(is.na(vol), "", paste0("Vol:", vol, " ml"))
  )
}
foods <- foods %>% mutate(size = make_size(weight_g, volume_ml))
## add Supraano brand_id from the mapping
foods$brand_id <- left_join(foods["brand"], brand_map, by = c("brand" = "shahrvand_brand"))$id
foods$category_id <- left_join(foods["sub_categ"],
                               supraano_cat[c("id", "name")],
                               by = c("sub_categ" = "name"))$id
foods <- foods %>% select(-c(raw_title, brand, current_price, weight_g, volume_ml, categ, sub_categ))
this_time = as.character(lubridate::now())
foods$created_at <- this_time
foods$updated_at <- this_time
foods$image <- paste0("http://supraano.com/storage/Product/sh_", foods$shahrvand_id, ".jpg")

write_csv(foods, path = "../data/foods_ready_for_db.csv")

## TODO: insert code that updates the database directly here
library(RMariaDB)
