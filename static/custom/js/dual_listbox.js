document.addEventListener("DOMContentLoaded", function () {
    const dualListbox = document.querySelector(".dual-list");
    if (dualListbox) {
        dualListbox.style.display = "flex";

        // Enhance the widget behavior
        const selectBoxes = document.querySelectorAll(".dual-list select");
        if (selectBoxes.length === 2) {
            const [availableBox, selectedBox] = selectBoxes;

            // Add buttons
            const container = dualListbox.parentElement;
            const buttonContainer = document.createElement("div");
            buttonContainer.innerHTML = `
                <button type="button" class="move-right">&gt;</button>
                <button type="button" class="move-left">&lt;</button>
            `;
            container.insertBefore(buttonContainer, selectedBox);

            const moveItems = (source, target) => {
                Array.from(source.selectedOptions).forEach(option => {
                    source.remove(option.index);
                    target.add(option);
                });
            };

            // Attach event listeners to buttons
            buttonContainer.querySelector(".move-right").addEventListener("click", () => {
                moveItems(availableBox, selectedBox);
            });
            buttonContainer.querySelector(".move-left").addEventListener("click", () => {
                moveItems(selectedBox, availableBox);
            });
        }
    }
});