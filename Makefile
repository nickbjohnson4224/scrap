CXXFLAGS := -std=c++11 -pedantic -Wall -Wextra -Werror
CXXFLAGS += -pipe -O3 -fomit-frame-pointer -march=native

SRCDIR := src
OBJDIR := build
BINDIR := bin
LIBDIR := lib
SUBDIRS := $(patsubst $(SRCDIR)/%,%,$(shell find $(SRCDIR) -mindepth 1 -type d))
OBJDIRS := $(OBJDIR) $(addprefix $(OBJDIR)/,$(SUBDIRS))

SRCFILES := $(shell find $(SRCDIR) -type f -name "*.cc")
HDRFILES := $(shell find $(SRCDIR) -type f -name "*.h")
OBJFILES := $(patsubst $(SRCDIR)%,$(OBJDIR)%.o,$(basename $(SRCFILES)))
BINFILES := $(BINDIR)/scrc

TARGETS := $(BINFILES)

.PHONY: clean

all: $(TARGETS)

$(OBJFILES): | $(OBJDIRS)
$(BINFILES): | $(BINDIR)

$(OBJDIRS):
	mkdir -p $(OBJDIRS)

$(BINDIR):
	mkdir -p $(BINDIR)

$(BINDIR)/scrc: $(OBJFILES)
	$(CXX) $(CXXFLAGS) -o $@ $(OBJFILES)

$(OBJDIR)/%.o: $(SRCDIR)/%.cc $(HDRFILES)
	$(CXX) $(CXXFLAGS) -o $@ -c $<	

clean:
	rm -r $(OBJDIR)
