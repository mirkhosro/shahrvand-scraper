library(tidyverse)
prod_type <- "toiletry"
prods <- read_csv(paste0("../data/", prod_type, "_GDoc.csv"))
brand_map <- read_csv(paste0("../data/", prod_type, "_brand_map_full.csv"))
## make sure it's the latest version
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
    ifelse(is.na(wgt), "", paste0(wgt, " گرمی")),
    ifelse(is.na(vol), "", paste0(vol, " میلیلیتری"))
  )
}
prods <- prods %>% mutate(size = make_size(weight_g, volume_ml))
## add Supraano brand_id from the mapping
prods$brand_id <- left_join(prods["brand"], brand_map, by = c("brand" = "shahrvand_brand"))$id
categ <- left_join(prods, supraano_cat[c("id", "name")],
                               by = c("sub_categ" = "name"))

## some sanity checks
null_id <- categ[is.na(categ$id), ]# %>% select(sub_categ) %>% unique
any(is.na(categ$id))
any(is.na(prods$brand_id))

prods$category_id <- categ$id
## remove columns that are not in DB table
prods <- prods %>% select(-c(raw_title, brand, current_price, weight_g, volume_ml, sub_categ))
if ("categ" %in% names(prods))
  prods <- prods %>% select(-categ)
## time stamps
this_time = as.character(lubridate::now())
prods$created_at <- this_time
prods$updated_at <- this_time
prods$image <- paste0("http://supraano.com/storage/Product/sh_", prods$shahrvand_id, ".jpg")
## save to file
write_csv(prods, path = paste0("../data/", prod_type, "_ready_for_db.csv"))

