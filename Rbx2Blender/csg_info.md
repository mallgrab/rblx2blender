Roblox will cache csg's if studio has access to the internet.

    <Item class="UnionOperation" referent="RBXFDFCED23C95748F6BD3A683553351F72">
        <Content name="AssetId"><url>https://www.roblox.com//asset/?id=7425729977</url></Content>

When requesting the asset we will get a binary xml where there's a MeshData tag.
    
    </roblox>PROPÍ��Ç������ö‚�������MeshData

The meshdata starts after 5 bytes.

    01 B2 08 00 00

And ends after PROP

Otherwise if there's no internet connection, csgv2 and v4 will both create a SharedString tag which is a md5 hash encoded with base64.

    <SharedString name="MeshData2">IHdT8J5Yet0yir5eahEwQw==</SharedString>

We then search for a SharedString tag that contains a md5 attribute.

    <SharedString md5="IHdT8J5Yet0yir5eahEwQw==">

csgv1 on the otherhand uses a BinaryString xml tag instead but works the same way as csgv2 and v4, the only difference is that the attribute value is MeshData instead of MeshData2

    <BinaryString name="MeshData">
    <string name="Name">MeshData</string>
				<BinaryString name="Value"><![CDATA[

The meshdata is encoded in base64 and xor'd with a key which the length is 32 bytes. Both the meshdata and the childdata (which is the history of the csg part which is used when seperating it) are both base64 encoded and xor'd. There really does not seem any logical reasoning behind the decision other than roblox really don't want people to fiddle with the format. From my own experimentations most changes on the csg format would end up not crashing the editor or the player so there are enough checks to not parse invalid csg data.